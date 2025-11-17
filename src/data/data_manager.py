"""
Unified Data Manager
Consolidates all data fetchers into a single interface for easy access.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional, Tuple
import yaml
from tqdm import tqdm

from .universe import UniverseManager
from .price_data import PriceDataFetcher
from .news_data import NewsDataFetcher
from .earnings_data import EarningsDataFetcher
from .analyst_data import AnalystDataFetcher


class DataManager:
    """
    Unified interface for all data operations.
    Manages stock universe, price data, and news data.
    """

    def __init__(
        self,
        config_path: str = "config/config.yaml",
        api_keys_path: str = "config/api_keys.yaml"
    ):
        """
        Initialize data manager.

        Args:
            config_path: Path to strategy configuration
            api_keys_path: Path to API keys configuration
        """
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize component managers
        cache_config = self.config.get('cache', {})
        cache_dir = cache_config.get('cache_dir', 'data/raw')

        self.universe_manager = UniverseManager(
            cache_dir=cache_dir,
            cache_days=7  # Universe changes infrequently
        )

        self.price_fetcher = PriceDataFetcher(
            api_keys_path=api_keys_path,
            cache_dir=f"{cache_dir}/prices",
            cache_days=cache_config.get('price_cache_days', 1)
        )

        self.news_fetcher = NewsDataFetcher(
            api_keys_path=api_keys_path,
            cache_dir=f"{cache_dir}/news",
            cache_hours=cache_config.get('news_cache_hours', 6)
        )

        self.earnings_fetcher = EarningsDataFetcher(
            cache_dir=f"{cache_dir}/earnings",
            cache_hours=cache_config.get('earnings_cache_hours', 24)
        )

        self.analyst_fetcher = AnalystDataFetcher(
            cache_dir=f"{cache_dir}/analyst",
            cache_hours=cache_config.get('analyst_cache_hours', 24)
        )

        logger.info("DataManager initialized")

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    # ========== Universe Methods ==========

    def get_universe(self) -> List[str]:
        """
        Get list of all ticker symbols in the universe.

        Returns:
            List of ticker symbols
        """
        return self.universe_manager.get_ticker_symbols()

    def get_universe_info(self) -> pd.DataFrame:
        """
        Get full universe information with metadata.

        Returns:
            DataFrame with ticker symbols and metadata
        """
        return self.universe_manager.get_sp500_tickers()

    def filter_by_sector(self, sector: str) -> List[str]:
        """
        Get tickers for a specific sector.

        Args:
            sector: GICS sector name

        Returns:
            List of ticker symbols
        """
        return self.universe_manager.get_tickers_by_sector(sector)

    # ========== Price Data Methods ==========

    def get_prices(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        show_progress: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get price data for multiple symbols.

        Args:
            symbols: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data
            show_progress: Show progress bar

        Returns:
            Dictionary mapping symbols to price DataFrames
        """
        source = self.config.get('data_sources', {}).get('price_data', 'auto')

        return self.price_fetcher.get_multiple_stocks(
            symbols=symbols,
            use_cache=use_cache,
            source=source,
            start_date=start_date,
            end_date=end_date,
            show_progress=show_progress
        )

    def get_prices_for_universe(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get price data for entire universe.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data

        Returns:
            Dictionary mapping symbols to price DataFrames
        """
        symbols = self.get_universe()
        logger.info(f"Fetching prices for {len(symbols)} stocks in universe")

        return self.get_prices(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache,
            show_progress=True
        )

    def calculate_returns(
        self,
        price_data: Dict[str, pd.DataFrame],
        periods: List[int] = [1, 21, 63, 252]
    ) -> Dict[str, pd.DataFrame]:
        """
        Calculate returns for price data.

        Args:
            price_data: Dictionary of price DataFrames
            periods: List of periods (in days) to calculate

        Returns:
            Dictionary of DataFrames with returns added
        """
        results = {}

        for symbol, df in price_data.items():
            if df is not None and not df.empty:
                results[symbol] = self.price_fetcher.calculate_returns(
                    df, periods=periods
                )

        return results

    # ========== News Data Methods ==========

    def get_news(
        self,
        symbols: List[str],
        lookback_days: int = 5,
        use_cache: bool = True
    ) -> Dict[str, List[Dict]]:
        """
        Get news for multiple symbols.

        Args:
            symbols: List of ticker symbols
            lookback_days: Number of days to look back (default: 5 for enhanced analysis)
            use_cache: Whether to use cached data

        Returns:
            Dictionary mapping symbols to lists of articles
        """
        results = {}

        news_sources = self.config.get('data_sources', {}).get('news_sources', {})
        enabled_sources = [
            source for source, enabled in news_sources.items()
            if enabled and source != 'alpha_vantage_sentiment'
        ]

        # Map config source names to fetcher names
        source_mapping = {
            'rss_feeds': 'rss',
            'newsapi': 'newsapi',
            'alpha_vantage_sentiment': 'alpha_vantage'
        }
        sources = [source_mapping.get(s, s) for s in enabled_sources]

        for symbol in tqdm(symbols, desc="Fetching news"):
            try:
                articles = self.news_fetcher.get_news(
                    symbol=symbol,
                    lookback_days=lookback_days,
                    sources=sources,
                    use_cache=use_cache
                )
                results[symbol] = articles
            except Exception as e:
                logger.error(f"Error fetching news for {symbol}: {e}")
                results[symbol] = []

        return results

    def get_news_summary(
        self,
        symbol: str,
        lookback_days: int = 5
    ) -> str:
        """
        Get formatted news summary for LLM analysis.

        Args:
            symbol: Stock ticker symbol
            lookback_days: Number of days to look back (default: 5 for enhanced analysis)

        Returns:
            Formatted text summary
        """
        return self.news_fetcher.get_news_summary(symbol, lookback_days)

    # ========== Earnings Methods ==========

    def get_earnings(
        self,
        symbols: List[str],
        use_cache: bool = True,
        show_progress: bool = False
    ) -> Dict[str, Dict]:
        """
        Get earnings data for multiple symbols.

        Args:
            symbols: List of ticker symbols
            use_cache: Whether to use cached data
            show_progress: Whether to show progress bar

        Returns:
            Dictionary mapping symbol -> earnings data
        """
        return self.earnings_fetcher.get_earnings(
            symbols,
            use_cache=use_cache,
            show_progress=show_progress
        )

    def get_earnings_for_symbol(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Get earnings data for a single symbol.

        Args:
            symbol: Ticker symbol
            use_cache: Whether to use cached data

        Returns:
            Dictionary with earnings data or None
        """
        return self.earnings_fetcher.get_earnings_for_symbol(
            symbol,
            use_cache=use_cache
        )

    def get_analyst_data(
        self,
        symbols: List[str],
        use_cache: bool = True,
        show_progress: bool = False
    ) -> Dict[str, Dict]:
        """
        Get analyst data for multiple symbols.

        Args:
            symbols: List of ticker symbols
            use_cache: Whether to use cached data
            show_progress: Whether to show progress bar

        Returns:
            Dictionary mapping symbol -> analyst data
        """
        return self.analyst_fetcher.get_analyst_data(
            symbols,
            use_cache=use_cache,
            show_progress=show_progress
        )

    def get_analyst_data_for_symbol(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Get analyst data for a single symbol.

        Args:
            symbol: Ticker symbol
            use_cache: Whether to use cached data

        Returns:
            Dictionary with analyst data or None
        """
        return self.analyst_fetcher.get_analyst_data_for_symbol(
            symbol,
            use_cache=use_cache
        )

    # ========== Combined Data Methods ==========

    def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_news: bool = True,
        news_lookback_days: int = 1
    ) -> Dict:
        """
        Get complete data package for a single stock.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for prices
            end_date: End date for prices
            include_news: Whether to include news
            news_lookback_days: News lookback period

        Returns:
            Dictionary with 'prices', 'info', and optionally 'news'
        """
        data = {}

        # Get ticker info
        data['info'] = self.universe_manager.get_ticker_info(symbol)

        # Get price data
        price_df = self.price_fetcher.get_price_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )

        if price_df is not None:
            # Calculate returns
            data['prices'] = self.price_fetcher.calculate_returns(price_df)
        else:
            data['prices'] = None

        # Get news if requested
        if include_news:
            data['news'] = self.news_fetcher.get_news(
                symbol=symbol,
                lookback_days=news_lookback_days
            )
            data['news_summary'] = self.news_fetcher.get_news_summary(
                symbol=symbol,
                lookback_days=news_lookback_days
            )

        return data

    def prepare_momentum_data(
        self,
        lookback_months: int = 12,
        exclude_recent_month: bool = True,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Prepare data for momentum calculation.

        Args:
            lookback_months: Number of months for momentum calculation
            exclude_recent_month: Whether to exclude most recent month
            end_date: End date for calculation (default: today)

        Returns:
            DataFrame with symbols and momentum returns
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Calculate start date
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # For momentum calculation, we need data from lookback_months ago
        # Plus 1 month if excluding recent
        total_lookback = lookback_months + (1 if exclude_recent_month else 0)
        start_dt = end_dt - timedelta(days=total_lookback * 30 + 30)  # Extra buffer
        start_date = start_dt.strftime('%Y-%m-%d')

        logger.info(f"Fetching data for momentum calculation: {start_date} to {end_date}")

        # Get universe
        symbols = self.get_universe()

        # Get prices
        price_data = self.get_prices(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            use_cache=True
        )

        # Calculate momentum for each stock
        momentum_data = []

        for symbol, df in price_data.items():
            if df is None or df.empty:
                continue

            try:
                # Filter to date range
                df = df[df.index <= end_date]

                if len(df) < 20:  # Need minimum data
                    continue

                # Calculate momentum return
                if exclude_recent_month:
                    # Exclude most recent month (21 trading days)
                    momentum_end = df.index[-22] if len(df) >= 22 else df.index[-1]
                else:
                    momentum_end = df.index[-1]

                # Get price from lookback_months ago
                momentum_start = momentum_end - timedelta(days=lookback_months * 30)

                # Get closest dates
                prices_before_end = df[df.index <= momentum_end]
                prices_after_start = df[df.index >= momentum_start]

                if len(prices_before_end) > 0 and len(prices_after_start) > 0:
                    start_price = prices_after_start['adjusted_close'].iloc[0]
                    end_price = prices_before_end['adjusted_close'].iloc[-1]

                    momentum_return = (end_price / start_price) - 1

                    momentum_data.append({
                        'symbol': symbol,
                        'momentum_return': momentum_return,
                        'start_date': prices_after_start.index[0],
                        'end_date': prices_before_end.index[-1],
                        'start_price': start_price,
                        'end_price': end_price
                    })

            except Exception as e:
                logger.warning(f"Error calculating momentum for {symbol}: {e}")

        # Create DataFrame
        momentum_df = pd.DataFrame(momentum_data)

        if not momentum_df.empty:
            # Sort by momentum return (descending)
            momentum_df = momentum_df.sort_values('momentum_return', ascending=False)
            momentum_df['rank'] = range(1, len(momentum_df) + 1)
            momentum_df['percentile'] = momentum_df['rank'] / len(momentum_df)

        logger.info(f"Calculated momentum for {len(momentum_df)} stocks")

        return momentum_df

    # ========== Data Quality & Validation ==========

    def validate_price_data(
        self,
        price_data: Dict[str, pd.DataFrame],
        min_days: int = 252
    ) -> Dict[str, bool]:
        """
        Validate price data quality.

        Args:
            price_data: Dictionary of price DataFrames
            min_days: Minimum number of days required

        Returns:
            Dictionary mapping symbols to validity (True/False)
        """
        validation = {}

        for symbol, df in price_data.items():
            if df is None or df.empty:
                validation[symbol] = False
                continue

            # Check minimum data
            if len(df) < min_days:
                validation[symbol] = False
                logger.warning(f"{symbol}: Insufficient data ({len(df)} < {min_days} days)")
                continue

            # Check for missing values in critical columns
            critical_cols = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume']
            existing_cols = [c for c in critical_cols if c in df.columns]

            if df[existing_cols].isna().any().any():
                validation[symbol] = False
                logger.warning(f"{symbol}: Missing values in price data")
                continue

            # Check for zero/negative prices
            price_cols = ['close', 'adjusted_close']
            for col in price_cols:
                if col in df.columns and (df[col] <= 0).any():
                    validation[symbol] = False
                    logger.warning(f"{symbol}: Invalid prices (zero or negative)")
                    break
            else:
                validation[symbol] = True

        valid_count = sum(validation.values())
        logger.info(f"Validated {len(price_data)} stocks: {valid_count} valid, {len(price_data) - valid_count} invalid")

        return validation

    # ========== Cache Management ==========

    def get_cache_summary(self) -> Dict:
        """Get summary of all cached data."""
        return {
            'universe': self.universe_manager.get_cache_info(),
            'prices': self.price_fetcher.get_cache_stats(),
            'news': self.news_fetcher.get_cache_stats()
        }

    def clear_all_caches(self):
        """Clear all cached data."""
        logger.warning("Clearing all caches...")

        response = input("This will delete all cached data. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Cancelled")
            return

        self.price_fetcher.clear_cache()
        self.news_fetcher.clear_cache()
        self.universe_manager.refresh_cache()

        logger.success("All caches cleared")

    # ========== Export/Import ==========

    def export_momentum_data(
        self,
        momentum_df: pd.DataFrame,
        output_path: str
    ):
        """
        Export momentum data to CSV.

        Args:
            momentum_df: Momentum DataFrame
            output_path: Path to save CSV
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        momentum_df.to_csv(output_file, index=False)
        logger.info(f"Exported momentum data to {output_file}")

    def export_price_data(
        self,
        price_data: Dict[str, pd.DataFrame],
        output_dir: str
    ):
        """
        Export price data to CSV files.

        Args:
            price_data: Dictionary of price DataFrames
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for symbol, df in price_data.items():
            if df is not None and not df.empty:
                file_path = output_path / f"{symbol}_prices.csv"
                df.to_csv(file_path)

        logger.info(f"Exported {len(price_data)} price files to {output_path}")


def main():
    """Test the data manager."""
    dm = DataManager()

    # Test universe
    logger.info("\n=== Testing Universe ===")
    universe = dm.get_universe()
    logger.info(f"Universe size: {len(universe)}")

    # Test price data for sample
    logger.info("\n=== Testing Price Data ===")
    sample_symbols = universe[:5]
    price_data = dm.get_prices(sample_symbols)
    logger.info(f"Fetched prices for {len(price_data)} stocks")

    # Validate price data
    validation = dm.validate_price_data(price_data, min_days=100)
    logger.info(f"Validation results: {validation}")

    # Test momentum calculation
    logger.info("\n=== Testing Momentum Calculation ===")
    momentum_df = dm.prepare_momentum_data(
        lookback_months=12,
        exclude_recent_month=True
    )
    logger.info(f"Momentum calculated for {len(momentum_df)} stocks")
    logger.info(f"\nTop 10 momentum stocks:\n{momentum_df.head(10)[['symbol', 'momentum_return', 'rank']]}")

    # Test news
    logger.info("\n=== Testing News Data ===")
    news_data = dm.get_news(sample_symbols[:2], lookback_days=1)
    for symbol, articles in news_data.items():
        logger.info(f"{symbol}: {len(articles)} articles")

    # Cache summary
    logger.info("\n=== Cache Summary ===")
    cache_summary = dm.get_cache_summary()
    logger.info(f"Cache summary: {cache_summary}")


if __name__ == "__main__":
    main()

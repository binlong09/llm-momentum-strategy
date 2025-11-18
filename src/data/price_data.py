"""
Stock Price Data Fetcher
Fetches historical stock prices from Alpha Vantage and yfinance with caching.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional, Tuple
import pickle
import time
import yaml
from alpha_vantage.timeseries import TimeSeries
import yfinance as yf
from tqdm import tqdm


class PriceDataFetcher:
    """Fetches and caches stock price data from multiple sources."""

    def __init__(
        self,
        api_keys_path: str = "config/api_keys.yaml",
        cache_dir: str = "data/raw/prices",
        cache_days: int = 1
    ):
        """
        Initialize price data fetcher.

        Args:
            api_keys_path: Path to API keys configuration
            cache_dir: Directory to store cached price data
            cache_days: Number of days to cache price data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days

        # Load API keys
        self.api_keys = self._load_api_keys(api_keys_path)

        # Initialize Alpha Vantage - check Streamlit secrets first, then YAML
        self.av_api_key = self._get_alpha_vantage_key()
        if self.av_api_key and self.av_api_key != "YOUR_ALPHA_VANTAGE_KEY_HERE":
            self.ts = TimeSeries(key=self.av_api_key, output_format='pandas')
            self.av_enabled = True
        else:
            self.ts = None
            self.av_enabled = False
            logger.warning("Alpha Vantage API key not configured, using yfinance only")

        # Rate limiting
        self.last_av_call = 0
        self.av_calls_per_minute = self.api_keys.get('rate_limits', {}).get('alpha_vantage_calls_per_minute', 5)
        self.min_call_interval = 60.0 / self.av_calls_per_minute

    def _load_api_keys(self, path: str) -> Dict:
        """Load API keys from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}

    def _get_alpha_vantage_key(self) -> Optional[str]:
        """
        Get Alpha Vantage API key with priority:
        1. Streamlit secrets (production)
        2. YAML config file (local development)
        """
        # Try Streamlit secrets first (production)
        try:
            import streamlit as st
            if 'alpha_vantage' in st.secrets and 'api_key' in st.secrets['alpha_vantage']:
                logger.info("Using Alpha Vantage API key from Streamlit secrets")
                return st.secrets['alpha_vantage']['api_key']
        except Exception:
            pass  # Streamlit not available or secrets not configured

        # Fall back to YAML config
        api_key = self.api_keys.get('alpha_vantage', {}).get('api_key')
        if api_key:
            logger.info("Using Alpha Vantage API key from config/api_keys.yaml")
        return api_key

    def _get_cache_path(self, symbol: str) -> Path:
        """Get cache file path for a symbol."""
        return self.cache_dir / f"{symbol}.pkl"

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid."""
        cache_file = self._get_cache_path(symbol)

        if not cache_file.exists():
            return False

        # Check file age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_days = (datetime.now() - file_time).days

        if age_days > self.cache_days:
            logger.debug(f"Cache for {symbol} is {age_days} days old (max: {self.cache_days})")
            return False

        return True

    def _load_from_cache(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load price data from cache."""
        cache_file = self._get_cache_path(symbol)

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"Loaded {symbol} from cache")
            return data
        except Exception as e:
            logger.error(f"Error loading cache for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, df: pd.DataFrame):
        """Save price data to cache."""
        cache_file = self._get_cache_path(symbol)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
            logger.debug(f"Saved {symbol} to cache")
        except Exception as e:
            logger.error(f"Error saving cache for {symbol}: {e}")

    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits."""
        if not self.av_enabled:
            return

        elapsed = time.time() - self.last_av_call
        if elapsed < self.min_call_interval:
            wait_time = self.min_call_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)

        self.last_av_call = time.time()

    def fetch_from_alpha_vantage(
        self,
        symbol: str,
        outputsize: str = 'full'
    ) -> Optional[pd.DataFrame]:
        """
        Fetch price data from Alpha Vantage.

        Args:
            symbol: Stock ticker symbol
            outputsize: 'compact' (100 days) or 'full' (20+ years)

        Returns:
            DataFrame with OHLCV data or None if error
        """
        if not self.av_enabled:
            return None

        try:
            self._wait_for_rate_limit()

            logger.info(f"Fetching {symbol} from Alpha Vantage...")
            data, meta_data = self.ts.get_daily_adjusted(
                symbol=symbol,
                outputsize=outputsize
            )

            # Rename columns
            data.columns = [
                'open', 'high', 'low', 'close',
                'adjusted_close', 'volume',
                'dividend', 'split_coefficient'
            ]

            # Convert index to datetime
            data.index = pd.to_datetime(data.index)
            data = data.sort_index()

            # Add symbol column
            data['symbol'] = symbol

            logger.success(f"Fetched {len(data)} days of data for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol} from Alpha Vantage: {e}")
            return None

    def fetch_from_yfinance(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "max"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch price data from yfinance.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Period to fetch if no dates ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')

        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            logger.info(f"Fetching {symbol} from yfinance...")

            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                data = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            else:
                data = ticker.history(period=period, auto_adjust=False)

            if data.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Rename columns to match Alpha Vantage format
            column_mapping = {
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Dividends': 'dividend',
                'Stock Splits': 'split_coefficient'
            }

            data = data.rename(columns=column_mapping)

            # Add adjusted_close if not present
            if 'adjusted_close' not in data.columns:
                # Calculate adjusted close from Close and adjustments
                if 'Adj Close' in ticker.history(period='1d').columns:
                    full_data = ticker.history(start=data.index.min(), end=data.index.max())
                    data['adjusted_close'] = full_data['Adj Close']
                else:
                    data['adjusted_close'] = data['close']

            # Add symbol column
            data['symbol'] = symbol

            logger.success(f"Fetched {len(data)} days of data for {symbol}")
            return data

        except Exception as e:
            logger.error(f"Error fetching {symbol} from yfinance: {e}")
            return None

    def get_price_data(
        self,
        symbol: str,
        use_cache: bool = True,
        source: str = 'auto',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get price data for a symbol with caching.

        Args:
            symbol: Stock ticker symbol
            use_cache: Whether to use cached data
            source: Data source ('alpha_vantage', 'yfinance', or 'auto')
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if error
        """
        # Check cache first
        if use_cache and self._is_cache_valid(symbol):
            data = self._load_from_cache(symbol)
            if data is not None:
                # Filter by date range if specified
                if start_date:
                    data = data[data.index >= start_date]
                if end_date:
                    data = data[data.index <= end_date]
                return data

        # Fetch from source
        data = None

        if source == 'alpha_vantage' or (source == 'auto' and self.av_enabled):
            data = self.fetch_from_alpha_vantage(symbol)

        if data is None and source in ['yfinance', 'auto']:
            data = self.fetch_from_yfinance(symbol, start_date, end_date)

        # Save to cache if successful
        if data is not None and not data.empty:
            self._save_to_cache(symbol, data)

            # Filter by date range if specified
            if start_date:
                data = data[data.index >= start_date]
            if end_date:
                data = data[data.index <= end_date]

        return data

    def get_multiple_stocks(
        self,
        symbols: List[str],
        use_cache: bool = True,
        source: str = 'auto',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch price data for multiple stocks.

        Args:
            symbols: List of ticker symbols
            use_cache: Whether to use cached data
            source: Data source ('alpha_vantage', 'yfinance', or 'auto')
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            show_progress: Show progress bar

        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}

        iterator = tqdm(symbols, desc="Fetching prices") if show_progress else symbols

        for symbol in iterator:
            data = self.get_price_data(
                symbol=symbol,
                use_cache=use_cache,
                source=source,
                start_date=start_date,
                end_date=end_date
            )

            if data is not None and not data.empty:
                results[symbol] = data
            else:
                logger.warning(f"Failed to fetch data for {symbol}")

        logger.info(f"Successfully fetched data for {len(results)}/{len(symbols)} stocks")
        return results

    def calculate_returns(
        self,
        df: pd.DataFrame,
        periods: List[int] = [1, 5, 21, 63, 252],
        price_col: str = 'adjusted_close'
    ) -> pd.DataFrame:
        """
        Calculate returns over various periods.

        Args:
            df: Price data DataFrame
            periods: List of periods (in days) to calculate returns
            price_col: Column to use for price

        Returns:
            DataFrame with return columns added
        """
        df = df.copy()

        for period in periods:
            col_name = f'return_{period}d'
            df[col_name] = df[price_col].pct_change(periods=period)

        return df

    def get_cache_stats(self) -> Dict:
        """Get statistics about cached data."""
        cache_files = list(self.cache_dir.glob("*.pkl"))

        if not cache_files:
            return {
                'num_cached': 0,
                'cache_dir': str(self.cache_dir),
                'total_size_mb': 0
            }

        total_size = sum(f.stat().st_size for f in cache_files)

        # Find oldest and newest
        file_times = [(f, datetime.fromtimestamp(f.stat().st_mtime)) for f in cache_files]
        oldest = min(file_times, key=lambda x: x[1])
        newest = max(file_times, key=lambda x: x[1])

        return {
            'num_cached': len(cache_files),
            'cache_dir': str(self.cache_dir),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_file': oldest[0].stem,
            'oldest_date': oldest[1].strftime('%Y-%m-%d %H:%M:%S'),
            'newest_file': newest[0].stem,
            'newest_date': newest[1].strftime('%Y-%m-%d %H:%M:%S')
        }

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached data.

        Args:
            symbol: If specified, clear only this symbol. Otherwise clear all.
        """
        if symbol:
            cache_file = self._get_cache_path(symbol)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Cleared cache for {symbol}")
        else:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            for f in cache_files:
                f.unlink()
            logger.info(f"Cleared {len(cache_files)} cached files")


def main():
    """Test the price data fetcher."""
    fetcher = PriceDataFetcher()

    # Test with a single stock
    logger.info("Testing with AAPL...")
    aapl = fetcher.get_price_data('AAPL', use_cache=False)

    if aapl is not None:
        logger.info(f"AAPL data shape: {aapl.shape}")
        logger.info(f"Date range: {aapl.index.min()} to {aapl.index.max()}")
        logger.info(f"Sample data:\n{aapl.tail()}")

        # Calculate returns
        aapl = fetcher.calculate_returns(aapl)
        logger.info(f"Returns calculated:\n{aapl[['adjusted_close', 'return_1d', 'return_21d']].tail()}")

    # Show cache stats
    stats = fetcher.get_cache_stats()
    logger.info(f"Cache stats: {stats}")


if __name__ == "__main__":
    main()

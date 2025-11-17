"""
Stock Universe Management
Fetches and manages the list of stocks to trade (S&P 500).
"""

import pandas as pd
import requests
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional
import pickle


class UniverseManager:
    """Manages stock universe (S&P 500) with caching."""

    def __init__(self, cache_dir: str = "data/raw", cache_days: int = 7):
        """
        Initialize universe manager.

        Args:
            cache_dir: Directory to store cached data
            cache_days: Number of days to cache ticker list
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days
        self.cache_file = self.cache_dir / "sp500_tickers.pkl"

    def get_sp500_tickers(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Get S&P 500 ticker list with metadata.

        Args:
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with columns: Symbol, Security, GICS Sector, GICS Sub-Industry, etc.
        """
        # Check cache first
        if use_cache and self._is_cache_valid():
            logger.info("Loading S&P 500 tickers from cache")
            return self._load_from_cache()

        logger.info("Fetching S&P 500 tickers from Wikipedia")
        try:
            # Fetch from Wikipedia
            df = self._fetch_from_wikipedia()

            # Save to cache
            self._save_to_cache(df)

            logger.success(f"Fetched {len(df)} S&P 500 tickers")
            return df

        except Exception as e:
            logger.error(f"Error fetching S&P 500 tickers: {e}")

            # Try to use cached data even if expired
            if self.cache_file.exists():
                logger.warning("Using expired cache as fallback")
                return self._load_from_cache()

            raise

    def _fetch_from_wikipedia(self) -> pd.DataFrame:
        """Fetch S&P 500 list from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        # Fetch HTML content with User-Agent header to avoid 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse tables from HTML content
        tables = pd.read_html(response.text)
        df = tables[0]  # First table contains the constituents

        # Clean up column names
        df.columns = df.columns.str.strip()

        # Rename for consistency
        column_mapping = {
            'Symbol': 'symbol',
            'Security': 'name',
            'GICS Sector': 'sector',
            'GICS Sub-Industry': 'sub_industry',
            'Headquarters Location': 'location',
            'Date added': 'date_added',
            'CIK': 'cik',
            'Founded': 'founded'
        }

        # Only rename columns that exist
        existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_mappings)

        # Handle special characters in tickers (e.g., BRK.B, BF.B)
        if 'symbol' in df.columns:
            df['symbol'] = df['symbol'].str.replace('.', '-', regex=False)

        # Add fetch timestamp
        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')

        return df

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache_file.exists():
            return False

        # Check file age
        file_time = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        age_days = (datetime.now() - file_time).days

        if age_days > self.cache_days:
            logger.debug(f"Cache is {age_days} days old (max: {self.cache_days})")
            return False

        return True

    def _load_from_cache(self) -> pd.DataFrame:
        """Load ticker list from cache."""
        with open(self.cache_file, 'rb') as f:
            data = pickle.load(f)
        return data

    def _save_to_cache(self, df: pd.DataFrame):
        """Save ticker list to cache."""
        with open(self.cache_file, 'wb') as f:
            pickle.dump(df, f)
        logger.debug(f"Saved ticker list to cache: {self.cache_file}")

    def get_tickers_by_sector(self, sector: str) -> List[str]:
        """
        Get tickers filtered by sector.

        Args:
            sector: GICS sector name

        Returns:
            List of ticker symbols
        """
        df = self.get_sp500_tickers()

        if 'sector' not in df.columns:
            logger.warning("Sector information not available")
            return []

        filtered = df[df['sector'] == sector]
        return filtered['symbol'].tolist()

    def get_all_sectors(self) -> List[str]:
        """Get list of all GICS sectors."""
        df = self.get_sp500_tickers()

        if 'sector' not in df.columns:
            return []

        return sorted(df['sector'].unique().tolist())

    def get_ticker_info(self, symbol: str) -> Optional[Dict]:
        """
        Get information for a specific ticker.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with ticker information or None if not found
        """
        df = self.get_sp500_tickers()

        # Handle both formats (A and A-)
        symbol_normalized = symbol.replace('-', '.')

        # Try exact match first
        if 'symbol' in df.columns:
            match = df[df['symbol'] == symbol]
            if match.empty:
                # Try with dot notation
                match = df[df['symbol'] == symbol_normalized]

            if not match.empty:
                return match.iloc[0].to_dict()

        logger.warning(f"Ticker {symbol} not found in S&P 500")
        return None

    def filter_valid_tickers(self, tickers: List[str]) -> List[str]:
        """
        Filter list to only include valid S&P 500 tickers.

        Args:
            tickers: List of ticker symbols to validate

        Returns:
            List of valid ticker symbols
        """
        df = self.get_sp500_tickers()

        if 'symbol' not in df.columns:
            logger.warning("Cannot validate tickers - symbol column missing")
            return tickers

        valid_tickers = set(df['symbol'].tolist())
        filtered = [t for t in tickers if t in valid_tickers]

        if len(filtered) < len(tickers):
            invalid = set(tickers) - set(filtered)
            logger.warning(f"Removed {len(invalid)} invalid tickers: {invalid}")

        return filtered

    def get_ticker_symbols(self) -> List[str]:
        """
        Get simple list of all S&P 500 ticker symbols.

        Returns:
            List of ticker symbols
        """
        df = self.get_sp500_tickers()

        if 'symbol' not in df.columns:
            logger.error("Symbol column not found")
            return []

        return df['symbol'].tolist()

    def refresh_cache(self):
        """Force refresh of cached ticker data."""
        logger.info("Forcing cache refresh")
        return self.get_sp500_tickers(use_cache=False)

    def get_cache_info(self) -> Dict:
        """Get information about cached data."""
        if not self.cache_file.exists():
            return {
                'cached': False,
                'file_path': str(self.cache_file)
            }

        file_time = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        age_days = (datetime.now() - file_time).days

        df = self._load_from_cache()

        return {
            'cached': True,
            'file_path': str(self.cache_file),
            'last_updated': file_time.strftime('%Y-%m-%d %H:%M:%S'),
            'age_days': age_days,
            'is_valid': self._is_cache_valid(),
            'num_tickers': len(df),
            'fetch_date': df['fetch_date'].iloc[0] if 'fetch_date' in df.columns else 'unknown'
        }


def main():
    """Test the universe manager."""
    manager = UniverseManager()

    # Get cache info
    cache_info = manager.get_cache_info()
    logger.info(f"Cache info: {cache_info}")

    # Fetch tickers
    df = manager.get_sp500_tickers()
    logger.info(f"Total tickers: {len(df)}")

    # Show sample
    logger.info(f"Sample tickers:\n{df.head(10)}")

    # Show sectors
    sectors = manager.get_all_sectors()
    logger.info(f"Sectors ({len(sectors)}): {sectors}")

    # Test ticker info
    if 'symbol' in df.columns and len(df) > 0:
        sample_ticker = df['symbol'].iloc[0]
        info = manager.get_ticker_info(sample_ticker)
        logger.info(f"Info for {sample_ticker}: {info}")


if __name__ == "__main__":
    main()

"""
Analyst Data Fetcher

Fetches analyst ratings, price targets, and estimates.
Uses yfinance for free analyst data.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional
import json
import time


class AnalystDataFetcher:
    """
    Fetches analyst ratings and estimates for stocks.

    Features:
    - Analyst recommendations (Buy/Hold/Sell)
    - Price targets (current, high, low, mean)
    - Earnings estimates (forward EPS)
    - Revenue estimates
    - Recommendation trends
    - Caching to reduce API calls
    """

    def __init__(
        self,
        cache_dir: str = "data/raw/analyst",
        cache_hours: int = 24
    ):
        """
        Initialize analyst data fetcher.

        Args:
            cache_dir: Directory for caching analyst data
            cache_hours: Hours to cache analyst data (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hours = cache_hours

        logger.info(f"AnalystDataFetcher initialized: cache_dir={cache_dir}, cache_hours={cache_hours}")

    def get_analyst_data(
        self,
        symbols: List[str],
        use_cache: bool = True,
        show_progress: bool = True
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
        analyst_data = {}

        if show_progress:
            from tqdm import tqdm
            symbols_iter = tqdm(symbols, desc="Fetching analyst data")
        else:
            symbols_iter = symbols

        for symbol in symbols_iter:
            try:
                data = self.get_analyst_data_for_symbol(
                    symbol,
                    use_cache=use_cache
                )
                if data:
                    analyst_data[symbol] = data
            except Exception as e:
                logger.debug(f"Error fetching analyst data for {symbol}: {e}")
                continue

        logger.info(f"Fetched analyst data for {len(analyst_data)}/{len(symbols)} symbols")
        return analyst_data

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
            Dictionary with analyst data or None if unavailable
        """
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(symbol)
            if cached_data:
                return cached_data

        try:
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)

            # Get various analyst data
            info = ticker.info

            # Try to get recommendations
            try:
                recommendations = ticker.recommendations
            except:
                recommendations = None

            # Try to get analyst price targets
            try:
                analyst_price_target = ticker.analyst_price_targets
            except:
                analyst_price_target = None

            # Build analyst summary
            analyst_summary = {
                'symbol': symbol,
                'fetched_at': datetime.now().isoformat(),

                # Current recommendation
                'recommendation': info.get('recommendationKey'),  # 'buy', 'hold', 'sell', etc.
                'recommendation_mean': info.get('recommendationMean'),  # 1=Strong Buy, 5=Sell

                # Number of analysts
                'number_of_analysts': info.get('numberOfAnalystOpinions'),

                # Price targets
                'target_high_price': info.get('targetHighPrice'),
                'target_low_price': info.get('targetLowPrice'),
                'target_mean_price': info.get('targetMeanPrice'),
                'target_median_price': info.get('targetMedianPrice'),
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),

                # Calculate upside
                'upside_potential': None,  # Will calculate below

                # Earnings estimates
                'forward_eps': info.get('forwardEps'),
                'forward_pe': info.get('forwardPE'),

                # Growth estimates
                'earnings_growth': info.get('earningsGrowth'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth'),

                # Recent recommendation trend (if available)
                'recent_upgrades': None,
                'recent_downgrades': None
            }

            # Calculate upside potential
            if analyst_summary['target_mean_price'] and analyst_summary['current_price']:
                current = analyst_summary['current_price']
                target = analyst_summary['target_mean_price']
                analyst_summary['upside_potential'] = (target - current) / current

            # Parse recent recommendations for upgrade/downgrade trends
            if recommendations is not None and not recommendations.empty:
                # Get last 90 days
                recent_date = datetime.now() - timedelta(days=90)

                # Filter recent recommendations
                if hasattr(recommendations.index, 'tz_localize'):
                    recent_recs = recommendations[recommendations.index >= recent_date]
                else:
                    # Handle timezone-aware datetime
                    recent_recs = recommendations

                if len(recent_recs) > 0:
                    # Count upgrades and downgrades
                    # yfinance provides 'To Grade' and 'From Grade' or 'Action'
                    if 'Action' in recent_recs.columns:
                        upgrades = recent_recs[recent_recs['Action'].str.contains('up', case=False, na=False)]
                        downgrades = recent_recs[recent_recs['Action'].str.contains('down', case=False, na=False)]
                        analyst_summary['recent_upgrades'] = len(upgrades)
                        analyst_summary['recent_downgrades'] = len(downgrades)

            # Only cache if we got some useful data
            if analyst_summary['recommendation'] or analyst_summary['target_mean_price']:
                if use_cache:
                    self._save_to_cache(symbol, analyst_summary)
                return analyst_summary
            else:
                logger.debug(f"No meaningful analyst data for {symbol}")
                return None

        except Exception as e:
            logger.debug(f"Error fetching analyst data for {symbol}: {e}")
            return None

    def _get_cache_path(self, symbol: str) -> Path:
        """Get cache file path for a symbol."""
        return self.cache_dir / f"{symbol}_analyst.json"

    def _load_from_cache(self, symbol: str) -> Optional[Dict]:
        """Load analyst data from cache if fresh."""
        cache_path = self._get_cache_path(symbol)

        if not cache_path.exists():
            return None

        try:
            # Check cache age
            cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if cache_age > timedelta(hours=self.cache_hours):
                return None

            # Load cached data
            with open(cache_path, 'r') as f:
                data = json.load(f)

            logger.debug(f"Loaded analyst data from cache for {symbol}")
            return data

        except Exception as e:
            logger.debug(f"Error loading cache for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, data: Dict):
        """Save analyst data to cache."""
        cache_path = self._get_cache_path(symbol)

        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved analyst data to cache for {symbol}")
        except Exception as e:
            logger.debug(f"Error saving cache for {symbol}: {e}")

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached analyst data.

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            cache_path = self._get_cache_path(symbol)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Cleared cache for {symbol}")
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*_analyst.json"):
                cache_file.unlink()
            logger.info("Cleared all analyst cache")


def main():
    """Test analyst fetcher."""
    logger.info("Testing AnalystDataFetcher...")

    fetcher = AnalystDataFetcher()

    # Test with a few stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    logger.info(f"\nFetching analyst data for {len(test_symbols)} stocks...")
    analyst_data = fetcher.get_analyst_data(test_symbols, use_cache=False, show_progress=True)

    # Display results
    for symbol, data in analyst_data.items():
        logger.info(f"\n{symbol}:")
        logger.info(f"  Recommendation: {data.get('recommendation', 'N/A')}")
        logger.info(f"  Number of Analysts: {data.get('number_of_analysts', 'N/A')}")

        if data.get('target_mean_price'):
            logger.info(f"  Target Price: ${data['target_mean_price']:.2f}")
            logger.info(f"  Current Price: ${data.get('current_price', 0):.2f}")
            if data.get('upside_potential') is not None:
                logger.info(f"  Upside: {data['upside_potential']*100:+.1f}%")

        if data.get('forward_eps'):
            logger.info(f"  Forward EPS: ${data['forward_eps']:.2f}")

        if data.get('earnings_growth'):
            logger.info(f"  Earnings Growth: {data['earnings_growth']*100:.1f}%")


if __name__ == "__main__":
    main()

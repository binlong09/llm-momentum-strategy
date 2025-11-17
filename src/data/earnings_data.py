"""
Earnings Data Fetcher

Fetches quarterly earnings data, revenue, EPS, and key metrics.
Uses yfinance (free) for earnings data.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Optional
import json
import time


class EarningsDataFetcher:
    """
    Fetches earnings and fundamental data for stocks.

    Features:
    - Quarterly earnings (revenue, EPS)
    - Year-over-year growth
    - Beat/miss vs estimates
    - Key metrics (margins, debt, etc.)
    - Caching to reduce API calls
    """

    def __init__(
        self,
        cache_dir: str = "data/raw/earnings",
        cache_hours: int = 24
    ):
        """
        Initialize earnings data fetcher.

        Args:
            cache_dir: Directory for caching earnings data
            cache_hours: Hours to cache earnings data (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hours = cache_hours

        logger.info(f"EarningsDataFetcher initialized: cache_dir={cache_dir}, cache_hours={cache_hours}")

    def get_earnings(
        self,
        symbols: List[str],
        use_cache: bool = True,
        show_progress: bool = True
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
        earnings_data = {}

        if show_progress:
            from tqdm import tqdm
            symbols_iter = tqdm(symbols, desc="Fetching earnings")
        else:
            symbols_iter = symbols

        for symbol in symbols_iter:
            try:
                earnings = self.get_earnings_for_symbol(
                    symbol,
                    use_cache=use_cache
                )
                if earnings:
                    earnings_data[symbol] = earnings
            except Exception as e:
                logger.debug(f"Error fetching earnings for {symbol}: {e}")
                continue

        logger.info(f"Fetched earnings for {len(earnings_data)}/{len(symbols)} symbols")
        return earnings_data

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
            Dictionary with earnings data or None if unavailable
        """
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(symbol)
            if cached_data:
                return cached_data

        try:
            # Fetch from yfinance
            ticker = yf.Ticker(symbol)

            # Get info for additional metrics
            info = ticker.info

            # Get quarterly financials for data
            try:
                quarterly_financials = ticker.quarterly_financials
                quarterly_income = ticker.quarterly_income_stmt
            except:
                quarterly_financials = None
                quarterly_income = None

            # Get earnings from quarterly_income_stmt (new yfinance API)
            # Look for "Net Income" row
            quarterly_earnings = None
            if quarterly_income is not None and not quarterly_income.empty:
                # Try to find net income row
                if 'Net Income' in quarterly_income.index:
                    quarterly_earnings = quarterly_income.loc['Net Income']
                elif 'NetIncome' in quarterly_income.index:
                    quarterly_earnings = quarterly_income.loc['NetIncome']

            # Get revenue from quarterly_income_stmt
            quarterly_revenue = None
            if quarterly_income is not None and not quarterly_income.empty:
                if 'Total Revenue' in quarterly_income.index:
                    quarterly_revenue = quarterly_income.loc['Total Revenue']
                elif 'TotalRevenue' in quarterly_income.index:
                    quarterly_revenue = quarterly_income.loc['TotalRevenue']

            if quarterly_earnings is None or (isinstance(quarterly_earnings, pd.Series) and quarterly_earnings.empty):
                logger.debug(f"No earnings data available for {symbol}")
                return None

            # Parse latest quarter (quarterly_earnings is now a Series with dates as index)
            latest_eps = quarterly_earnings.iloc[0] if len(quarterly_earnings) > 0 else None
            prev_eps = quarterly_earnings.iloc[1] if len(quarterly_earnings) > 1 else None
            year_ago_eps = quarterly_earnings.iloc[4] if len(quarterly_earnings) > 4 else None

            # Parse revenue
            latest_revenue = quarterly_revenue.iloc[0] if quarterly_revenue is not None and len(quarterly_revenue) > 0 else None
            year_ago_revenue = quarterly_revenue.iloc[4] if quarterly_revenue is not None and len(quarterly_revenue) > 4 else None

            # Calculate growth rates
            qoq_growth = None
            yoy_eps_growth = None
            revenue_yoy_growth = None

            if latest_eps is not None and prev_eps is not None and prev_eps != 0:
                qoq_growth = (latest_eps - prev_eps) / abs(prev_eps)

            if latest_eps is not None and year_ago_eps is not None and year_ago_eps != 0:
                yoy_eps_growth = (latest_eps - year_ago_eps) / abs(year_ago_eps)

            if latest_revenue is not None and year_ago_revenue is not None and year_ago_revenue != 0:
                revenue_yoy_growth = (latest_revenue - year_ago_revenue) / year_ago_revenue

            # Calculate EPS per share (divide net income by shares outstanding)
            shares_outstanding = info.get('sharesOutstanding')
            latest_eps_per_share = None
            if latest_eps is not None and shares_outstanding:
                latest_eps_per_share = latest_eps / shares_outstanding

            # Build earnings summary
            earnings_summary = {
                'symbol': symbol,
                'latest_quarter_date': quarterly_earnings.index[0].strftime('%Y-%m-%d') if len(quarterly_earnings) > 0 else None,
                'latest_eps': float(latest_eps_per_share) if latest_eps_per_share is not None else info.get('trailingEps'),
                'latest_revenue': float(latest_revenue) if latest_revenue is not None else None,
                'qoq_growth': float(qoq_growth) if qoq_growth is not None else None,
                'yoy_eps_growth': float(yoy_eps_growth) if yoy_eps_growth is not None else None,
                'yoy_revenue_growth': float(revenue_yoy_growth) if revenue_yoy_growth is not None else None,

                # Key metrics from info
                'profit_margin': info.get('profitMargins'),
                'operating_margin': info.get('operatingMargins'),
                'gross_margin': info.get('grossMargins'),
                'debt_to_equity': info.get('debtToEquity'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),

                # Estimates (if available)
                'forward_eps': info.get('forwardEps'),
                'trailing_eps': info.get('trailingEps'),

                'fetched_at': datetime.now().isoformat()
            }

            # Save to cache
            if use_cache:
                self._save_to_cache(symbol, earnings_summary)

            return earnings_summary

        except Exception as e:
            logger.debug(f"Error fetching earnings for {symbol}: {e}")
            return None

    def _get_cache_path(self, symbol: str) -> Path:
        """Get cache file path for a symbol."""
        return self.cache_dir / f"{symbol}_earnings.json"

    def _load_from_cache(self, symbol: str) -> Optional[Dict]:
        """Load earnings data from cache if fresh."""
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

            logger.debug(f"Loaded earnings from cache for {symbol}")
            return data

        except Exception as e:
            logger.debug(f"Error loading cache for {symbol}: {e}")
            return None

    def _save_to_cache(self, symbol: str, data: Dict):
        """Save earnings data to cache."""
        cache_path = self._get_cache_path(symbol)

        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved earnings to cache for {symbol}")
        except Exception as e:
            logger.debug(f"Error saving cache for {symbol}: {e}")

    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear cached earnings data.

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
            for cache_file in self.cache_dir.glob("*_earnings.json"):
                cache_file.unlink()
            logger.info("Cleared all earnings cache")


def main():
    """Test earnings fetcher."""
    logger.info("Testing EarningsDataFetcher...")

    fetcher = EarningsDataFetcher()

    # Test with a few stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']

    logger.info(f"\nFetching earnings for {len(test_symbols)} stocks...")
    earnings_data = fetcher.get_earnings(test_symbols, use_cache=False, show_progress=True)

    # Display results
    for symbol, data in earnings_data.items():
        logger.info(f"\n{symbol}:")
        logger.info(f"  Latest Quarter: {data.get('latest_quarter_date')}")
        logger.info(f"  EPS: ${data.get('latest_eps', 'N/A')}")
        logger.info(f"  Revenue: ${data.get('latest_revenue', 'N/A'):,.0f}" if data.get('latest_revenue') else "  Revenue: N/A")
        logger.info(f"  YoY EPS Growth: {data.get('yoy_eps_growth', 'N/A'):.1%}" if data.get('yoy_eps_growth') is not None else "  YoY EPS Growth: N/A")
        logger.info(f"  YoY Revenue Growth: {data.get('yoy_revenue_growth', 'N/A'):.1%}" if data.get('yoy_revenue_growth') is not None else "  YoY Revenue Growth: N/A")
        logger.info(f"  Profit Margin: {data.get('profit_margin', 'N/A'):.1%}" if data.get('profit_margin') is not None else "  Profit Margin: N/A")


if __name__ == "__main__":
    main()

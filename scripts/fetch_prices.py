#!/usr/bin/env python3
"""
Fetch Price Data Utility
Fetch and cache stock price data for analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.price_data import PriceDataFetcher
from src.data.universe import UniverseManager
from loguru import logger
import argparse
from datetime import datetime, timedelta


def fetch_sample_stocks(fetcher, num_stocks=10):
    """Fetch data for a sample of S&P 500 stocks."""
    logger.info(f"Fetching sample of {num_stocks} stocks...")

    # Get S&P 500 tickers
    universe = UniverseManager()
    all_tickers = universe.get_ticker_symbols()

    # Take first N stocks
    sample_tickers = all_tickers[:num_stocks]

    logger.info(f"Sample tickers: {sample_tickers}")

    # Fetch data
    results = fetcher.get_multiple_stocks(
        symbols=sample_tickers,
        use_cache=True,
        source='auto',
        show_progress=True
    )

    # Show summary
    print("\n" + "=" * 60)
    print("📊 Fetch Summary")
    print("=" * 60)

    for symbol, df in results.items():
        if df is not None and not df.empty:
            date_range = f"{df.index.min().date()} to {df.index.max().date()}"
            print(f"{symbol:6s}: {len(df):5d} days ({date_range})")

    print(f"\nSuccessfully fetched: {len(results)}/{len(sample_tickers)} stocks")


def fetch_by_sector(fetcher, sector_name, max_stocks=None):
    """Fetch data for all stocks in a sector."""
    logger.info(f"Fetching stocks from sector: {sector_name}")

    # Get tickers for sector
    universe = UniverseManager()
    tickers = universe.get_tickers_by_sector(sector_name)

    if not tickers:
        logger.error(f"No tickers found for sector: {sector_name}")
        return

    if max_stocks:
        tickers = tickers[:max_stocks]

    logger.info(f"Fetching {len(tickers)} stocks from {sector_name}")

    # Fetch data
    results = fetcher.get_multiple_stocks(
        symbols=tickers,
        use_cache=True,
        source='auto',
        show_progress=True
    )

    print(f"\n✅ Fetched {len(results)}/{len(tickers)} stocks from {sector_name}")


def fetch_specific_stocks(fetcher, symbols, start_date=None, end_date=None):
    """Fetch data for specific stock symbols."""
    logger.info(f"Fetching {len(symbols)} specific stocks...")

    results = fetcher.get_multiple_stocks(
        symbols=symbols,
        use_cache=True,
        source='auto',
        start_date=start_date,
        end_date=end_date,
        show_progress=True
    )

    # Show detailed info
    print("\n" + "=" * 60)
    print("📊 Detailed Results")
    print("=" * 60)

    for symbol in symbols:
        if symbol in results:
            df = results[symbol]
            print(f"\n{symbol}:")
            print(f"  Date range: {df.index.min().date()} to {df.index.max().date()}")
            print(f"  Total days: {len(df)}")
            print(f"  Latest price: ${df['adjusted_close'].iloc[-1]:.2f}")
            print(f"  Recent data:")
            print(df[['open', 'high', 'low', 'close', 'adjusted_close', 'volume']].tail(3).to_string())
        else:
            print(f"\n{symbol}: ❌ Failed to fetch")


def show_cache_stats(fetcher):
    """Display cache statistics."""
    stats = fetcher.get_cache_stats()

    print("\n" + "=" * 60)
    print("💾 Cache Statistics")
    print("=" * 60)

    if stats['num_cached'] == 0:
        print("📂 Cache is empty")
        print(f"   Location: {stats['cache_dir']}")
    else:
        print(f"📂 Cache directory: {stats['cache_dir']}")
        print(f"📊 Cached stocks: {stats['num_cached']}")
        print(f"💽 Total size: {stats['total_size_mb']:.2f} MB")
        print(f"🕐 Oldest: {stats['oldest_file']} ({stats['oldest_date']})")
        print(f"🕑 Newest: {stats['newest_file']} ({stats['newest_date']})")


def clear_cache(fetcher, symbol=None):
    """Clear cache."""
    if symbol:
        logger.info(f"Clearing cache for {symbol}...")
        fetcher.clear_cache(symbol)
    else:
        logger.info("Clearing all cached price data...")
        response = input("Are you sure? This will delete all cached price data (y/N): ")
        if response.lower() == 'y':
            fetcher.clear_cache()
            logger.success("Cache cleared!")
        else:
            logger.info("Cancelled")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Fetch stock price data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch sample of 10 stocks
  python scripts/fetch_prices.py --sample 10

  # Fetch specific stocks
  python scripts/fetch_prices.py --symbols AAPL MSFT GOOGL

  # Fetch all tech stocks
  python scripts/fetch_prices.py --sector "Information Technology"

  # Fetch with date range
  python scripts/fetch_prices.py --symbols AAPL --start 2020-01-01 --end 2023-12-31

  # Show cache stats
  python scripts/fetch_prices.py --stats

  # Clear cache
  python scripts/fetch_prices.py --clear-cache
        """
    )

    parser.add_argument('--sample', type=int,
                       help='Fetch a random sample of N stocks')
    parser.add_argument('--symbols', nargs='+',
                       help='Specific stock symbols to fetch')
    parser.add_argument('--sector', type=str,
                       help='Fetch all stocks from a sector')
    parser.add_argument('--max-stocks', type=int,
                       help='Maximum stocks to fetch from sector')
    parser.add_argument('--start', type=str,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--stats', action='store_true',
                       help='Show cache statistics')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear all cached price data')
    parser.add_argument('--clear-symbol', type=str,
                       help='Clear cache for specific symbol')
    parser.add_argument('--source', type=str, default='auto',
                       choices=['auto', 'alpha_vantage', 'yfinance'],
                       help='Data source (default: auto)')

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = PriceDataFetcher()

    # Execute commands
    if args.stats:
        show_cache_stats(fetcher)

    elif args.clear_cache:
        clear_cache(fetcher)

    elif args.clear_symbol:
        clear_cache(fetcher, args.clear_symbol)

    elif args.sample:
        fetch_sample_stocks(fetcher, args.sample)
        show_cache_stats(fetcher)

    elif args.sector:
        fetch_by_sector(fetcher, args.sector, args.max_stocks)
        show_cache_stats(fetcher)

    elif args.symbols:
        fetch_specific_stocks(fetcher, args.symbols, args.start, args.end)
        show_cache_stats(fetcher)

    else:
        parser.print_help()
        print("\n💡 Use --help for usage examples")


if __name__ == "__main__":
    main()

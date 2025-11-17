#!/usr/bin/env python3
"""
Fetch News Data Utility
Fetch and display news articles for stocks.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.news_data import NewsDataFetcher
from src.data.universe import UniverseManager
from loguru import logger
import argparse
from datetime import datetime


def fetch_for_symbol(fetcher, symbol, lookback_days=1, show_details=True):
    """Fetch and display news for a single symbol."""
    logger.info(f"Fetching news for {symbol} (last {lookback_days} days)...")

    articles = fetcher.get_news(
        symbol=symbol,
        lookback_days=lookback_days,
        use_cache=True
    )

    print("\n" + "=" * 80)
    print(f"📰 News for {symbol}")
    print("=" * 80)

    if not articles:
        print(f"No news found for {symbol} in the last {lookback_days} day(s)")
        return

    print(f"Found {len(articles)} articles:\n")

    for i, article in enumerate(articles, 1):
        pub_date = article.get('published')
        date_str = pub_date.strftime('%Y-%m-%d %H:%M') if pub_date else 'Unknown'

        print(f"{i}. [{date_str}] {article.get('title')}")
        print(f"   Source: {article.get('source')} | Feed: {article.get('feed', 'N/A')}")

        if show_details:
            summary = article.get('summary', '')
            if summary:
                # Truncate long summaries
                summary_clean = summary[:200] + "..." if len(summary) > 200 else summary
                print(f"   {summary_clean}")

        print(f"   URL: {article.get('url')}")

        # Show sentiment if available
        if 'sentiment' in article and article['sentiment']:
            sent = article['sentiment']
            print(f"   Sentiment: {sent.get('label')} ({sent.get('score'):.3f})")

        print()


def fetch_summary(fetcher, symbol, lookback_days=1):
    """Fetch and display formatted summary for LLM."""
    summary = fetcher.get_news_summary(symbol, lookback_days=lookback_days)

    print("\n" + "=" * 80)
    print(f"📝 News Summary for {symbol} (for LLM)")
    print("=" * 80)
    print(summary)
    print("=" * 80)


def fetch_for_multiple_stocks(fetcher, symbols, lookback_days=1):
    """Fetch news for multiple stocks."""
    results = {}

    for symbol in symbols:
        try:
            articles = fetcher.get_news(
                symbol=symbol,
                lookback_days=lookback_days,
                use_cache=True
            )
            results[symbol] = len(articles)
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            results[symbol] = 0

    # Show summary
    print("\n" + "=" * 80)
    print("📊 News Fetch Summary")
    print("=" * 80)

    for symbol, count in results.items():
        print(f"{symbol:6s}: {count:3d} articles")

    total = sum(results.values())
    print(f"\nTotal: {total} articles across {len(symbols)} stocks")


def show_cache_stats(fetcher):
    """Display cache statistics."""
    stats = fetcher.get_cache_stats()

    print("\n" + "=" * 80)
    print("💾 News Cache Statistics")
    print("=" * 80)

    if stats['num_cached'] == 0:
        print("📂 Cache is empty")
        print(f"   Location: {stats['cache_dir']}")
    else:
        print(f"📂 Cache directory: {stats['cache_dir']}")
        print(f"📊 Cached queries: {stats['num_cached']}")
        print(f"💽 Total size: {stats['total_size_mb']:.2f} MB")


def clear_cache(fetcher):
    """Clear news cache."""
    logger.info("Clearing news cache...")
    response = input("Are you sure? This will delete all cached news data (y/N): ")
    if response.lower() == 'y':
        fetcher.clear_cache()
        logger.success("Cache cleared!")
    else:
        logger.info("Cancelled")


def test_sources(fetcher, symbol):
    """Test each news source individually."""
    print("\n" + "=" * 80)
    print(f"🧪 Testing News Sources for {symbol}")
    print("=" * 80)

    # Test RSS
    print("\n📡 Testing RSS Feeds...")
    rss_articles = fetcher.fetch_from_rss(symbol, lookback_days=1)
    print(f"   Found {len(rss_articles)} articles from RSS")

    # Test NewsAPI
    if fetcher.newsapi_enabled:
        print("\n📰 Testing NewsAPI...")
        newsapi_articles = fetcher.fetch_from_newsapi(symbol, lookback_days=1)
        print(f"   Found {len(newsapi_articles)} articles from NewsAPI")
    else:
        print("\n📰 NewsAPI: Disabled")

    # Test Alpha Vantage
    if fetcher.av_enabled:
        print("\n📈 Testing Alpha Vantage News Sentiment...")
        av_articles = fetcher.fetch_from_alpha_vantage(symbol, lookback_days=1)
        print(f"   Found {len(av_articles)} articles from Alpha Vantage")
    else:
        print("\n📈 Alpha Vantage: API key not configured")

    print("\n" + "=" * 80)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Fetch news data for stocks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch news for a single stock
  python scripts/fetch_news.py --symbol AAPL

  # Fetch news with 3-day lookback
  python scripts/fetch_news.py --symbol AAPL --days 3

  # Fetch for multiple stocks
  python scripts/fetch_news.py --symbols AAPL MSFT GOOGL

  # Get formatted summary for LLM
  python scripts/fetch_news.py --symbol AAPL --summary

  # Test all news sources
  python scripts/fetch_news.py --symbol AAPL --test-sources

  # Show cache stats
  python scripts/fetch_news.py --stats

  # Clear cache
  python scripts/fetch_news.py --clear-cache
        """
    )

    parser.add_argument('--symbol', type=str,
                       help='Stock symbol to fetch news for')
    parser.add_argument('--symbols', nargs='+',
                       help='Multiple stock symbols')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to look back (default: 1)')
    parser.add_argument('--summary', action='store_true',
                       help='Show formatted summary for LLM')
    parser.add_argument('--no-details', action='store_true',
                       help='Hide article summaries')
    parser.add_argument('--test-sources', action='store_true',
                       help='Test each news source individually')
    parser.add_argument('--stats', action='store_true',
                       help='Show cache statistics')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear news cache')

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = NewsDataFetcher()

    # Execute commands
    if args.stats:
        show_cache_stats(fetcher)

    elif args.clear_cache:
        clear_cache(fetcher)

    elif args.test_sources and args.symbol:
        test_sources(fetcher, args.symbol)

    elif args.summary and args.symbol:
        fetch_summary(fetcher, args.symbol, args.days)

    elif args.symbol:
        fetch_for_symbol(fetcher, args.symbol, args.days, not args.no_details)

    elif args.symbols:
        fetch_for_multiple_stocks(fetcher, args.symbols, args.days)

    else:
        parser.print_help()
        print("\n💡 Use --help for usage examples")


if __name__ == "__main__":
    main()

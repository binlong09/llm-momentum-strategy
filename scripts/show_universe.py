#!/usr/bin/env python3
"""
Show S&P 500 Universe Information
Quick utility to view ticker list, sectors, and universe statistics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.universe import UniverseManager
from loguru import logger
import argparse


def show_cache_info(manager):
    """Display cache information."""
    cache_info = manager.get_cache_info()

    print("\n" + "=" * 60)
    print("📦 Cache Information")
    print("=" * 60)

    if cache_info['cached']:
        print(f"✅ Cache exists: {cache_info['file_path']}")
        print(f"📅 Last updated: {cache_info['last_updated']}")
        print(f"⏰ Age: {cache_info['age_days']} days")
        print(f"✓  Valid: {'Yes' if cache_info['is_valid'] else 'No (expired)'}")
        print(f"📊 Tickers: {cache_info['num_tickers']}")
    else:
        print(f"❌ No cache found at: {cache_info['file_path']}")


def show_sectors(manager):
    """Display sector breakdown."""
    df = manager.get_sp500_tickers()

    print("\n" + "=" * 60)
    print("📊 Sector Breakdown")
    print("=" * 60)

    if 'sector' not in df.columns:
        print("⚠️  Sector information not available")
        return

    sector_counts = df['sector'].value_counts()

    for sector, count in sector_counts.items():
        pct = (count / len(df)) * 100
        print(f"{sector:30s}: {count:3d} stocks ({pct:5.1f}%)")

    print(f"\n{'Total':30s}: {len(df):3d} stocks")


def show_sample(manager, n=20):
    """Display sample tickers."""
    df = manager.get_sp500_tickers()

    print("\n" + "=" * 60)
    print(f"📋 Sample Tickers (first {n})")
    print("=" * 60)

    # Select relevant columns
    cols_to_show = []
    for col in ['symbol', 'name', 'sector', 'sub_industry']:
        if col in df.columns:
            cols_to_show.append(col)

    if cols_to_show:
        print(df[cols_to_show].head(n).to_string(index=False))
    else:
        print(df.head(n))


def show_sector_detail(manager, sector_name):
    """Display tickers for a specific sector."""
    tickers = manager.get_tickers_by_sector(sector_name)

    print("\n" + "=" * 60)
    print(f"📊 {sector_name} Sector")
    print("=" * 60)

    if not tickers:
        print(f"No tickers found for sector: {sector_name}")
        return

    print(f"Found {len(tickers)} tickers:")

    # Get full info
    df = manager.get_sp500_tickers()
    sector_df = df[df['sector'] == sector_name]

    cols_to_show = []
    for col in ['symbol', 'name', 'sub_industry']:
        if col in sector_df.columns:
            cols_to_show.append(col)

    if cols_to_show:
        print(sector_df[cols_to_show].to_string(index=False))
    else:
        print('\n'.join(tickers))


def search_ticker(manager, query):
    """Search for tickers by name or symbol."""
    df = manager.get_sp500_tickers()

    print("\n" + "=" * 60)
    print(f"🔍 Search Results for: '{query}'")
    print("=" * 60)

    # Search in symbol and name
    mask = False
    if 'symbol' in df.columns:
        mask |= df['symbol'].str.contains(query, case=False, na=False)
    if 'name' in df.columns:
        mask |= df['name'].str.contains(query, case=False, na=False)

    results = df[mask]

    if len(results) == 0:
        print(f"No results found for '{query}'")
        return

    print(f"Found {len(results)} result(s):\n")

    cols_to_show = []
    for col in ['symbol', 'name', 'sector', 'sub_industry']:
        if col in results.columns:
            cols_to_show.append(col)

    if cols_to_show:
        print(results[cols_to_show].to_string(index=False))
    else:
        print(results)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Show S&P 500 universe information',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--refresh', action='store_true',
                       help='Force refresh of ticker data from Wikipedia')
    parser.add_argument('--sectors', action='store_true',
                       help='Show sector breakdown')
    parser.add_argument('--sector', type=str,
                       help='Show tickers for a specific sector')
    parser.add_argument('--sample', type=int, default=20,
                       help='Number of sample tickers to show (default: 20)')
    parser.add_argument('--search', type=str,
                       help='Search for tickers by name or symbol')
    parser.add_argument('--list-sectors', action='store_true',
                       help='List all available sectors')

    args = parser.parse_args()

    # Initialize manager
    manager = UniverseManager()

    # Force refresh if requested
    if args.refresh:
        logger.info("Forcing cache refresh...")
        manager.refresh_cache()

    # Show cache info
    show_cache_info(manager)

    # Execute requested actions
    if args.list_sectors:
        sectors = manager.get_all_sectors()
        print("\n" + "=" * 60)
        print("📊 Available Sectors")
        print("=" * 60)
        for i, sector in enumerate(sectors, 1):
            print(f"{i}. {sector}")

    elif args.sector:
        show_sector_detail(manager, args.sector)

    elif args.search:
        search_ticker(manager, args.search)

    elif args.sectors:
        show_sectors(manager)

    else:
        # Default: show overview
        show_sectors(manager)
        show_sample(manager, args.sample)

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

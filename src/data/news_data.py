"""
News Data Fetcher
Fetches news articles from multiple sources for stock analysis.
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
import feedparser
import requests
from newsapi import NewsApiClient
from bs4 import BeautifulSoup
from urllib.parse import quote
import hashlib


class NewsDataFetcher:
    """Fetches news articles from multiple sources with caching."""

    def __init__(
        self,
        api_keys_path: str = "config/api_keys.yaml",
        cache_dir: str = "data/raw/news",
        cache_hours: int = 6
    ):
        """
        Initialize news data fetcher.

        Args:
            api_keys_path: Path to API keys configuration
            cache_dir: Directory to store cached news data
            cache_hours: Number of hours to cache news data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_hours = cache_hours

        # Load API keys
        self.api_keys = self._load_api_keys(api_keys_path)

        # Initialize NewsAPI if enabled
        newsapi_config = self.api_keys.get('newsapi', {})
        if newsapi_config.get('enabled', False):
            api_key = newsapi_config.get('api_key')
            if api_key and api_key != "YOUR_NEWSAPI_KEY_HERE":
                self.newsapi = NewsApiClient(api_key=api_key)
                self.newsapi_enabled = True
                logger.info("NewsAPI enabled")
            else:
                self.newsapi = None
                self.newsapi_enabled = False
        else:
            self.newsapi = None
            self.newsapi_enabled = False

        # Alpha Vantage for news sentiment
        self.av_api_key = self.api_keys.get('alpha_vantage', {}).get('api_key')
        self.av_enabled = (
            self.av_api_key and
            self.av_api_key != "YOUR_ALPHA_VANTAGE_KEY_HERE"
        )

        # RSS feed sources
        self.rss_feeds = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Top news
            "https://www.marketwatch.com/rss/topstories",
            "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",  # WSJ Markets
        ]

    def _load_api_keys(self, path: str) -> Dict:
        """Load API keys from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        # Use hash of key to create filename
        key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"news_{key_hash}.pkl"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        cache_file = self._get_cache_path(cache_key)

        if not cache_file.exists():
            return False

        # Check file age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - file_time).total_seconds() / 3600

        if age_hours > self.cache_hours:
            logger.debug(f"Cache expired (age: {age_hours:.1f}h, max: {self.cache_hours}h)")
            return False

        return True

    def _load_from_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Load news data from cache."""
        cache_file = self._get_cache_path(cache_key)

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            logger.debug(f"Loaded {len(data)} articles from cache")
            return data
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return None

    def _save_to_cache(self, cache_key: str, articles: List[Dict]):
        """Save news data to cache."""
        cache_file = self._get_cache_path(cache_key)

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(articles, f)
            logger.debug(f"Saved {len(articles)} articles to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def fetch_from_rss(
        self,
        symbol: str,
        lookback_days: int = 1
    ) -> List[Dict]:
        """
        Fetch news from RSS feeds.

        Args:
            symbol: Stock ticker symbol
            lookback_days: Number of days to look back

        Returns:
            List of article dictionaries
        """
        articles = []
        cutoff_date = datetime.now() - timedelta(days=lookback_days)

        # Yahoo Finance specific feed
        yahoo_feed = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"

        feeds_to_check = [yahoo_feed] + self.rss_feeds

        for feed_url in feeds_to_check:
            try:
                logger.debug(f"Fetching RSS feed: {feed_url}")
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = datetime(*entry.updated_parsed[:6])

                    # Skip if too old
                    if pub_date and pub_date < cutoff_date:
                        continue

                    # Check if article mentions the symbol
                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))

                    # Only include if symbol is mentioned (for general feeds)
                    if feed_url != yahoo_feed:
                        if symbol.upper() not in (title + summary).upper():
                            continue

                    article = {
                        'source': 'rss',
                        'feed': feed_url,
                        'title': title,
                        'summary': summary,
                        'url': entry.get('link', ''),
                        'published': pub_date,
                        'symbol': symbol
                    }

                    articles.append(article)

            except Exception as e:
                logger.warning(f"Error fetching RSS feed {feed_url}: {e}")

        logger.info(f"Fetched {len(articles)} articles from RSS for {symbol}")
        return articles

    def fetch_from_newsapi(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        lookback_days: int = 1
    ) -> List[Dict]:
        """
        Fetch news from NewsAPI.

        Args:
            symbol: Stock ticker symbol
            company_name: Company name for better search
            lookback_days: Number of days to look back

        Returns:
            List of article dictionaries
        """
        if not self.newsapi_enabled:
            return []

        articles = []

        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=lookback_days)

            # Search query
            query = f"{symbol}"
            if company_name:
                query += f" OR {company_name}"

            logger.debug(f"NewsAPI query: {query}")

            # Fetch articles
            response = self.newsapi.get_everything(
                q=query,
                from_param=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d'),
                language='en',
                sort_by='publishedAt',
                page_size=100
            )

            if response.get('status') == 'ok':
                for article_data in response.get('articles', []):
                    # Parse date
                    pub_date = None
                    if article_data.get('publishedAt'):
                        try:
                            pub_date = datetime.strptime(
                                article_data['publishedAt'],
                                '%Y-%m-%dT%H:%M:%SZ'
                            )
                        except:
                            pass

                    article = {
                        'source': 'newsapi',
                        'feed': article_data.get('source', {}).get('name', 'Unknown'),
                        'title': article_data.get('title', ''),
                        'summary': article_data.get('description', ''),
                        'content': article_data.get('content', ''),
                        'url': article_data.get('url', ''),
                        'published': pub_date,
                        'symbol': symbol
                    }

                    articles.append(article)

                logger.info(f"Fetched {len(articles)} articles from NewsAPI for {symbol}")
            else:
                logger.warning(f"NewsAPI error: {response.get('message')}")

        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")

        return articles

    def fetch_from_alpha_vantage(
        self,
        symbol: str,
        lookback_days: int = 1
    ) -> List[Dict]:
        """
        Fetch news sentiment from Alpha Vantage.

        Args:
            symbol: Stock ticker symbol
            lookback_days: Number of days to look back

        Returns:
            List of article dictionaries with sentiment scores
        """
        if not self.av_enabled:
            return []

        articles = []

        try:
            # Calculate time range
            time_from = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y%m%dT%H%M')
            time_to = datetime.now().strftime('%Y%m%dT%H%M')

            url = (
                f"https://www.alphavantage.co/query?"
                f"function=NEWS_SENTIMENT&"
                f"tickers={symbol}&"
                f"time_from={time_from}&"
                f"time_to={time_to}&"
                f"limit=200&"
                f"apikey={self.av_api_key}"
            )

            logger.debug(f"Fetching Alpha Vantage news for {symbol}")
            response = requests.get(url, timeout=30)
            data = response.json()

            if 'feed' in data:
                for item in data['feed']:
                    # Parse date
                    pub_date = None
                    if item.get('time_published'):
                        try:
                            pub_date = datetime.strptime(
                                item['time_published'],
                                '%Y%m%dT%H%M%S'
                            )
                        except:
                            pass

                    # Extract sentiment for this ticker
                    ticker_sentiment = None
                    for ts in item.get('ticker_sentiment', []):
                        if ts.get('ticker') == symbol:
                            ticker_sentiment = {
                                'score': float(ts.get('ticker_sentiment_score', 0)),
                                'label': ts.get('ticker_sentiment_label', 'Neutral')
                            }
                            break

                    article = {
                        'source': 'alpha_vantage',
                        'feed': ', '.join([a.get('name', '') for a in item.get('authors', [])]),
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'published': pub_date,
                        'symbol': symbol,
                        'sentiment': ticker_sentiment,
                        'overall_sentiment': {
                            'score': float(item.get('overall_sentiment_score', 0)),
                            'label': item.get('overall_sentiment_label', 'Neutral')
                        }
                    }

                    articles.append(article)

                logger.info(f"Fetched {len(articles)} articles from Alpha Vantage for {symbol}")
            elif 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
            else:
                logger.warning(f"Unexpected Alpha Vantage response: {data}")

        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")

        return articles

    def get_news(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        lookback_days: int = 1,
        sources: List[str] = ['rss', 'newsapi', 'alpha_vantage'],
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Get news articles from multiple sources.

        Args:
            symbol: Stock ticker symbol
            company_name: Company name for better search
            lookback_days: Number of days to look back
            sources: List of sources to use
            use_cache: Whether to use cached data

        Returns:
            List of article dictionaries
        """
        # Create cache key
        cache_key = f"{symbol}_{lookback_days}_{'_'.join(sorted(sources))}"

        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                logger.info(f"Using cached news for {symbol} ({len(cached)} articles)")
                return cached

        # Fetch from sources
        all_articles = []

        if 'rss' in sources:
            all_articles.extend(self.fetch_from_rss(symbol, lookback_days))

        if 'newsapi' in sources and self.newsapi_enabled:
            all_articles.extend(
                self.fetch_from_newsapi(symbol, company_name, lookback_days)
            )

        if 'alpha_vantage' in sources and self.av_enabled:
            all_articles.extend(
                self.fetch_from_alpha_vantage(symbol, lookback_days)
            )

        # Deduplicate by URL and title
        unique_articles = self._deduplicate_articles(all_articles)

        # Sort by published date (newest first)
        unique_articles.sort(
            key=lambda x: x.get('published') or datetime.min,
            reverse=True
        )

        # Save to cache
        if unique_articles:
            self._save_to_cache(cache_key, unique_articles)

        logger.success(f"Fetched {len(unique_articles)} unique articles for {symbol}")
        return unique_articles

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on URL and title."""
        seen_urls = set()
        seen_titles = set()
        unique = []

        for article in articles:
            url = article.get('url', '').strip()
            title = article.get('title', '').strip().lower()

            # Skip if we've seen this URL or very similar title
            if url and url in seen_urls:
                continue
            if title and title in seen_titles:
                continue

            unique.append(article)

            if url:
                seen_urls.add(url)
            if title:
                seen_titles.add(title)

        logger.debug(f"Deduplicated {len(articles)} -> {len(unique)} articles")
        return unique

    def get_news_summary(
        self,
        symbol: str,
        lookback_days: int = 1,
        max_chars: int = 2000
    ) -> str:
        """
        Get a text summary of recent news for LLM analysis.

        Args:
            symbol: Stock ticker symbol
            lookback_days: Number of days to look back
            max_chars: Maximum characters in summary

        Returns:
            Formatted text summary of news
        """
        articles = self.get_news(symbol, lookback_days=lookback_days)

        if not articles:
            return f"No recent news found for {symbol}"

        summary_parts = [f"Recent news for {symbol}:"]

        for i, article in enumerate(articles[:10], 1):  # Max 10 articles
            pub_date = article.get('published')
            date_str = pub_date.strftime('%Y-%m-%d') if pub_date else 'Unknown'

            title = article.get('title', 'No title')
            summary = article.get('summary', '')

            part = f"\n{i}. [{date_str}] {title}"
            if summary and len(summary) > 0:
                # Truncate long summaries
                summary_clean = summary[:200] + "..." if len(summary) > 200 else summary
                part += f"\n   {summary_clean}"

            # Check if adding this would exceed max_chars
            current_length = len('\n'.join(summary_parts))
            if current_length + len(part) > max_chars:
                summary_parts.append(f"\n... ({len(articles) - i + 1} more articles)")
                break

            summary_parts.append(part)

        return '\n'.join(summary_parts)

    def get_cache_stats(self) -> Dict:
        """Get statistics about cached news data."""
        cache_files = list(self.cache_dir.glob("news_*.pkl"))

        if not cache_files:
            return {
                'num_cached': 0,
                'cache_dir': str(self.cache_dir),
                'total_size_mb': 0
            }

        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'num_cached': len(cache_files),
            'cache_dir': str(self.cache_dir),
            'total_size_mb': total_size / (1024 * 1024)
        }

    def clear_cache(self):
        """Clear all cached news data."""
        cache_files = list(self.cache_dir.glob("news_*.pkl"))
        for f in cache_files:
            f.unlink()
        logger.info(f"Cleared {len(cache_files)} cached news files")


def main():
    """Test the news data fetcher."""
    fetcher = NewsDataFetcher()

    # Test with a sample stock
    logger.info("Testing news fetch for AAPL...")
    articles = fetcher.get_news('AAPL', company_name='Apple', lookback_days=2)

    logger.info(f"Found {len(articles)} articles")

    if articles:
        logger.info("\nSample articles:")
        for i, article in enumerate(articles[:5], 1):
            logger.info(f"\n{i}. {article.get('title')}")
            logger.info(f"   Source: {article.get('source')}")
            logger.info(f"   Published: {article.get('published')}")
            logger.info(f"   URL: {article.get('url')}")

        # Test summary
        logger.info("\n" + "=" * 60)
        logger.info("News Summary:")
        logger.info("=" * 60)
        summary = fetcher.get_news_summary('AAPL', lookback_days=2)
        print(summary)

    # Cache stats
    stats = fetcher.get_cache_stats()
    logger.info(f"\nCache stats: {stats}")


if __name__ == "__main__":
    main()

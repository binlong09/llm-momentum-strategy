"""
News Monitor - Track news for portfolio holdings
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
from src.data import DataManager
from src.llm import LLMScorer


class NewsMonitor:
    """Monitor news for portfolio holdings and detect red flags."""

    # Keywords that indicate serious problems
    RED_FLAG_KEYWORDS = [
        'fraud', 'scandal', 'investigation', 'sec probe', 'lawsuit',
        'bankruptcy', 'default', 'delisting', 'halt', 'suspended',
        'accounting irregularities', 'insider trading', 'indictment',
        'criminal charges', 'class action', 'whistleblower'
    ]

    WARNING_KEYWORDS = [
        'downgrade', 'missed earnings', 'revenue miss', 'guidance cut',
        'layoffs', 'restructuring', 'ceo departure', 'exec departure',
        'recall', 'fine', 'settlement', 'loss', 'decline'
    ]

    POSITIVE_KEYWORDS = [
        'upgrade', 'beat earnings', 'revenue beat', 'guidance raise',
        'acquisition', 'partnership', 'new product', 'expansion',
        'record', 'growth', 'innovation', 'breakthrough'
    ]

    def __init__(self):
        self.data_manager = DataManager()
        self.llm_scorer = LLMScorer()

    def monitor_holdings(
        self,
        symbols: List[str],
        lookback_days: int = 1,
        use_llm: bool = False
    ) -> pd.DataFrame:
        """
        Monitor news for all holdings.

        Args:
            symbols: List of ticker symbols
            lookback_days: Days to look back for news
            use_llm: Whether to use LLM for sentiment analysis

        Returns:
            DataFrame with news alerts and sentiment
        """
        logger.info(f"Monitoring news for {len(symbols)} holdings...")

        # Fetch news
        news_data = self.data_manager.get_news(
            symbols=symbols,
            lookback_days=lookback_days,
            use_cache=False  # Always get fresh news
        )

        results = []

        for symbol in symbols:
            articles = news_data.get(symbol, [])

            if not articles:
                results.append({
                    'symbol': symbol,
                    'num_articles': 0,
                    'sentiment': 'neutral',
                    'alert_level': 'none',
                    'red_flags': [],
                    'warnings': [],
                    'positive_signals': [],
                    'summary': 'No recent news'
                })
                continue

            # Analyze news
            analysis = self._analyze_news(articles, symbol, use_llm)
            results.append(analysis)

        results_df = pd.DataFrame(results)

        # Sort by alert level priority
        alert_priority = {'critical': 0, 'warning': 1, 'info': 2, 'none': 3}
        results_df['_priority'] = results_df['alert_level'].map(alert_priority)
        results_df = results_df.sort_values('_priority').drop('_priority', axis=1)

        logger.success(f"News monitoring complete: {len(results_df)} stocks analyzed")

        return results_df

    def _analyze_news(
        self,
        articles: List[Dict],
        symbol: str,
        use_llm: bool
    ) -> Dict:
        """Analyze news articles for a single stock with context-aware detection."""

        # Find articles that actually mention the symbol/company
        # This reduces false positives from general market news
        company_variations = [
            symbol.lower(),
            symbol.upper(),
            f"${symbol.upper()}",  # Ticker with $
        ]

        # For single-letter tickers (like C for Citigroup), use more specific variations
        # to avoid matching the letter "c" in random words
        if len(symbol) == 1:
            # Map common single-letter tickers to company names
            ticker_to_company = {
                'C': 'citigroup',
                'F': 'ford',
                'T': 'at&t',
            }
            company_name = ticker_to_company.get(symbol.upper())
            if company_name:
                company_variations = [
                    company_name,
                    company_name.title(),
                    f"${symbol.upper()}",  # Keep ticker with $ prefix
                    f" {symbol.upper()} ",  # Space-separated ticker
                    f"({symbol.upper()})",  # Ticker in parentheses
                ]

        # Analyze each article for relevance and keywords
        red_flag_evidence = []
        warning_evidence = []
        positive_evidence = []

        for article in articles:
            title = article.get('title', '')
            summary = article.get('summary', '')
            url = article.get('url', '')
            pub_date = article.get('published', '')

            # Combine title and summary
            full_text = f"{title} {summary}".lower()

            # Check if article is actually about this company
            is_relevant = any(var in full_text for var in company_variations)

            # If not relevant, only flag if it's in the title (more specific)
            if not is_relevant and not any(var in title.lower() for var in company_variations):
                # Skip this article - likely general market news
                continue

            # Check for red flags WITH context
            for keyword in self.RED_FLAG_KEYWORDS:
                if keyword in full_text:
                    # Extract context around the keyword (50 chars before/after)
                    idx = full_text.find(keyword)
                    context_start = max(0, idx - 50)
                    context_end = min(len(full_text), idx + len(keyword) + 50)
                    context = full_text[context_start:context_end]

                    # Only flag if company is mentioned near the keyword (within context)
                    if any(var in context for var in company_variations):
                        red_flag_evidence.append({
                            'keyword': keyword,
                            'article_title': title,
                            'url': url,
                            'published': pub_date,
                            'context': context.strip(),
                            'relevance': 'high'
                        })
                    elif is_relevant:
                        # Article is about company but keyword might be general
                        red_flag_evidence.append({
                            'keyword': keyword,
                            'article_title': title,
                            'url': url,
                            'published': pub_date,
                            'context': context.strip(),
                            'relevance': 'medium'
                        })

            # Check for warnings WITH context
            for keyword in self.WARNING_KEYWORDS:
                if keyword in full_text and is_relevant:
                    idx = full_text.find(keyword)
                    context_start = max(0, idx - 50)
                    context_end = min(len(full_text), idx + len(keyword) + 50)
                    context = full_text[context_start:context_end]

                    warning_evidence.append({
                        'keyword': keyword,
                        'article_title': title,
                        'url': url,
                        'published': pub_date,
                        'context': context.strip()
                    })

            # Check for positive signals
            for keyword in self.POSITIVE_KEYWORDS:
                if keyword in full_text and is_relevant:
                    idx = full_text.find(keyword)
                    context_start = max(0, idx - 50)
                    context_end = min(len(full_text), idx + len(keyword) + 50)
                    context = full_text[context_start:context_end]

                    positive_evidence.append({
                        'keyword': keyword,
                        'article_title': title,
                        'url': url,
                        'published': pub_date,
                        'context': context.strip()
                    })

        # Filter red flags by relevance - only high relevance triggers critical
        high_relevance_red_flags = [
            e for e in red_flag_evidence if e.get('relevance') == 'high'
        ]

        # Extract unique keywords
        red_flags = list(set([e['keyword'] for e in high_relevance_red_flags]))
        warnings = list(set([e['keyword'] for e in warning_evidence]))
        positive = list(set([e['keyword'] for e in positive_evidence]))

        # Determine alert level (stricter now)
        if len(high_relevance_red_flags) >= 2:  # Need at least 2 high-relevance mentions
            alert_level = 'critical'
            sentiment = 'very_negative'
        elif len(high_relevance_red_flags) == 1:
            alert_level = 'warning'  # Downgrade single red flag to warning
            sentiment = 'negative'
        elif len(warnings) >= 3:
            alert_level = 'warning'
            sentiment = 'negative'
        elif warnings:
            alert_level = 'info'  # Downgrade single warning to info
            sentiment = 'negative'
        elif len(positive) >= 3:
            alert_level = 'info'
            sentiment = 'very_positive'
        elif positive:
            alert_level = 'info'
            sentiment = 'positive'
        else:
            alert_level = 'none'
            sentiment = 'neutral'

        # Get LLM sentiment if requested
        llm_sentiment = None
        if use_llm and len(articles) > 0:
            try:
                from src.llm.prompts import PromptTemplate
                news_summary = PromptTemplate.format_news_for_prompt(articles)

                # Fetch analyst data for enhanced context
                analyst_data = None
                try:
                    from src.data.analyst_data import AnalystDataFetcher
                    analyst_fetcher = AnalystDataFetcher()
                    analyst_data = analyst_fetcher.get_analyst_data(symbol)
                except Exception as e:
                    logger.debug(f"Could not fetch analyst data for {symbol}: {e}")

                # Use basic scoring with analyst context
                # Note: score_stock will format analyst_data internally
                score = self.llm_scorer.score_stock(
                    symbol=symbol,
                    news_summary=news_summary,
                    momentum_return=0.0,
                    analyst_data=analyst_data  # Pass raw dict, not formatted string
                )
                if score is not None:
                    llm_sentiment = score[1]  # Normalized score
                    # Adjust sentiment based on LLM
                    if llm_sentiment < -0.5:
                        sentiment = 'very_negative'
                        if alert_level == 'none':
                            alert_level = 'warning'
                    elif llm_sentiment < -0.2:
                        sentiment = 'negative'
                    elif llm_sentiment > 0.5:
                        sentiment = 'very_positive'
                    elif llm_sentiment > 0.2:
                        sentiment = 'positive'
            except Exception as e:
                logger.warning(f"LLM sentiment failed for {symbol}: {e}")

        # Create detailed summary with evidence
        summary_parts = []
        if red_flags:
            summary_parts.append(f"🚨 Red flags: {', '.join(red_flags[:3])}")
        if warnings:
            summary_parts.append(f"⚠️ Warnings: {', '.join(warnings[:3])}")
        if positive:
            summary_parts.append(f"✅ Positive: {', '.join(positive[:3])}")

        if not summary_parts and len(articles) > 0:
            # Show first article headline
            summary_parts.append(articles[0].get('title', 'Recent news available'))

        return {
            'symbol': symbol,
            'num_articles': len(articles),
            'sentiment': sentiment,
            'alert_level': alert_level,
            'red_flags': red_flags,
            'warnings': warnings,
            'positive_signals': positive,
            'llm_sentiment_score': llm_sentiment,
            'summary': ' | '.join(summary_parts[:2]),  # Limit summary length
            'latest_article': articles[0].get('title', '') if articles else '',
            'latest_url': articles[0].get('url', '') if articles else '',
            # Evidence with URLs and context for justification
            'red_flag_evidence': red_flag_evidence,
            'warning_evidence': warning_evidence,
            'positive_evidence': positive_evidence
        }

    def get_critical_alerts(self, monitoring_df: pd.DataFrame) -> pd.DataFrame:
        """Get only critical alerts that need immediate attention."""
        return monitoring_df[monitoring_df['alert_level'] == 'critical']

    def get_top_movers_news(
        self,
        holdings_df: pd.DataFrame,
        threshold: float = 0.05
    ) -> List[str]:
        """
        Get symbols that moved significantly and need news check.

        Args:
            holdings_df: Holdings with price change data
            threshold: Minimum absolute price change (default 5%)

        Returns:
            List of symbols to monitor
        """
        if 'price_change_pct' not in holdings_df.columns:
            return []

        # Find stocks with significant moves
        significant_moves = holdings_df[
            abs(holdings_df['price_change_pct']) >= threshold * 100
        ]

        return significant_moves['symbol'].tolist()

    def generate_daily_report(
        self,
        monitoring_df: pd.DataFrame
    ) -> str:
        """
        Generate a daily news summary report.

        Args:
            monitoring_df: News monitoring results

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("DAILY NEWS MONITORING REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        report.append("=" * 80)
        report.append("")

        # Critical alerts
        critical = monitoring_df[monitoring_df['alert_level'] == 'critical']
        if len(critical) > 0:
            report.append("🚨 CRITICAL ALERTS - IMMEDIATE ATTENTION REQUIRED")
            report.append("-" * 80)
            for _, row in critical.iterrows():
                report.append(f"  {row['symbol']}: {row['summary']}")
                report.append(f"    Red flags: {', '.join(row['red_flags'])}")
                report.append("")

        # Warnings
        warnings = monitoring_df[monitoring_df['alert_level'] == 'warning']
        if len(warnings) > 0:
            report.append("⚠️  WARNINGS - MONITOR CLOSELY")
            report.append("-" * 80)
            for _, row in warnings.head(5).iterrows():  # Top 5 warnings
                report.append(f"  {row['symbol']}: {row['summary']}")
                report.append("")

        # Positive news
        positive = monitoring_df[monitoring_df['sentiment'].isin(['positive', 'very_positive'])]
        if len(positive) > 0:
            report.append("✅ POSITIVE DEVELOPMENTS")
            report.append("-" * 80)
            for _, row in positive.head(3).iterrows():  # Top 3 positive
                report.append(f"  {row['symbol']}: {row['summary']}")
                report.append("")

        # Summary stats
        report.append("=" * 80)
        report.append("SUMMARY STATISTICS")
        report.append("=" * 80)
        report.append(f"  Total stocks monitored: {len(monitoring_df)}")
        report.append(f"  Critical alerts: {len(critical)}")
        report.append(f"  Warnings: {len(warnings)}")
        report.append(f"  Positive news: {len(positive)}")
        report.append(f"  Neutral/No news: {len(monitoring_df) - len(critical) - len(warnings) - len(positive)}")
        report.append("")

        return "\n".join(report)

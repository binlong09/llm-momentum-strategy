"""
LLM Prompt Templates
Implements prompt templates for stock scoring based on news and momentum.
"""

from typing import Dict, Optional
from datetime import datetime


class PromptTemplate:
    """
    Manages prompt templates for LLM-based stock scoring.

    Based on the paper's optimal parameters:
    - 1-day news lookback
    - 21-day forecast horizon (monthly rebalancing)
    - Score range: 0-1 (normalized to [-1, 1])
    """

    @staticmethod
    def basic_prompt(
        symbol: str,
        news_summary: str,
        momentum_return: Optional[float] = None,
        earnings_summary: Optional[str] = None,
        analyst_summary: Optional[str] = None,
        forecast_days: int = 21
    ) -> str:
        """
        Basic prompt template.

        Args:
            symbol: Stock ticker symbol
            news_summary: Recent news summary
            momentum_return: 12-month momentum return (optional)
            earnings_summary: Formatted earnings data (optional)
            analyst_summary: Formatted analyst data (optional)
            forecast_days: Forecast horizon in days

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"You are a financial analyst evaluating stock: {symbol}",
            ""
        ]

        # Add momentum if available
        if momentum_return is not None:
            prompt_parts.extend([
                "Momentum Signal:",
                f"12-Month Return: {momentum_return:.2%}",
                ""
            ])

        # Add earnings if available
        if earnings_summary:
            prompt_parts.extend([
                earnings_summary,
                ""
            ])

        # Add analyst data if available
        if analyst_summary:
            prompt_parts.extend([
                analyst_summary,
                ""
            ])

        # Add news
        prompt_parts.extend([
            "Recent News:",
            news_summary if news_summary else "No recent news available.",
            ""
        ])

        prompt_parts.extend([
            f"Based on the information above, predict the stock's performance over the next {forecast_days} trading days (~1 month).",
            "",
            "Provide a score from 0 to 1 where:",
            "- 0 = Very negative outlook (expect significant decline)",
            "- 0.5 = Neutral outlook (expect flat performance)",
            "- 1 = Very positive outlook (expect significant gain)",
            "",
            "Respond with ONLY a single number between 0 and 1, with no additional text or explanation."
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def advanced_prompt(
        symbol: str,
        news_summary: str,
        momentum_return: Optional[float] = None,
        company_name: Optional[str] = None,
        sector: Optional[str] = None,
        earnings_summary: Optional[str] = None,
        analyst_summary: Optional[str] = None,
        forecast_days: int = 21
    ) -> str:
        """
        Advanced prompt with additional context.

        Args:
            symbol: Stock ticker symbol
            news_summary: Recent news summary
            momentum_return: 12-month momentum return
            company_name: Company name
            sector: Market sector
            earnings_summary: Formatted earnings data (optional)
            analyst_summary: Formatted analyst data (optional)
            forecast_days: Forecast horizon

        Returns:
            Formatted prompt string
        """
        # Header
        prompt_parts = [
            "You are an expert quantitative analyst at a hedge fund.",
            "",
            "TASK: Evaluate the following stock for inclusion in a momentum-based portfolio.",
            ""
        ]

        # Company info
        prompt_parts.append("COMPANY INFORMATION:")
        prompt_parts.append(f"Ticker: {symbol}")
        if company_name:
            prompt_parts.append(f"Name: {company_name}")
        if sector:
            prompt_parts.append(f"Sector: {sector}")
        prompt_parts.append("")

        # Momentum
        if momentum_return is not None:
            prompt_parts.extend([
                "MOMENTUM SIGNAL:",
                f"12-Month Return: {momentum_return:.2%}",
                "This stock is in the top 20% by momentum (already pre-selected).",
                ""
            ])

        # Earnings data (if available)
        if earnings_summary:
            prompt_parts.extend([
                earnings_summary,
                ""
            ])

        # Analyst data (if available)
        if analyst_summary:
            prompt_parts.extend([
                analyst_summary,
                ""
            ])

        # News
        prompt_parts.extend([
            "RECENT NEWS (Last 3-7 Days):",
            "Priority given to: Earnings reports, M&A activity, regulatory news, major announcements",
            news_summary if news_summary else "No significant news in the last week.",
            ""
        ])

        # Instructions
        prompt_parts.extend([
            "ANALYSIS INSTRUCTIONS:",
            f"1. Evaluate the stock's likely performance over the next {forecast_days} trading days (~1 month)",
            "2. Consider (in order of importance):",
            "   a. Recent earnings/revenue trends and growth rates (from earnings data or news)",
            "   b. Major company announcements or developments",
            "   c. News sentiment and potential market impact",
            "   d. Momentum continuation probability (stock already has strong momentum)",
            "   e. Any regulatory, competitive, or operational risks mentioned",
            "",
            "3. Key question: Given this stock ALREADY has strong 12-month momentum,",
            "   how likely is this momentum to CONTINUE based on recent fundamentals and news?",
            "",
            "SCORING:",
            "Provide a numerical score from 0 to 1:",
            "- 0.0-0.3: Negative outlook - data suggests momentum will likely reverse",
            "- 0.4-0.6: Neutral outlook - data is mixed or inconclusive",
            "- 0.7-0.9: Positive outlook - data supports momentum continuation",
            "- 0.9-1.0: Very positive outlook - strong catalysts support acceleration",
            "",
            "IMPORTANT: Respond with ONLY a single decimal number between 0 and 1.",
            "Do not include any explanation, reasoning, or additional text."
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def research_prompt(
        symbol: str,
        news_summary: str,
        momentum_return: Optional[float] = None,
        earnings_summary: Optional[str] = None,
        analyst_summary: Optional[str] = None,
        forecast_days: int = 21
    ) -> str:
        """
        Research-oriented prompt with explanation request.
        Used for understanding LLM reasoning with detailed analysis.

        Args:
            symbol: Stock ticker
            news_summary: Recent news
            momentum_return: 12-month momentum
            earnings_summary: Formatted earnings data
            analyst_summary: Formatted analyst data
            forecast_days: Forecast horizon

        Returns:
            Formatted prompt with explanation request
        """
        prompt_parts = [
            f"You are an expert financial analyst evaluating stock: {symbol}",
            "",
            "Your task: Provide a detailed analysis and outlook for this stock.",
            ""
        ]

        # Add momentum if available
        if momentum_return is not None:
            prompt_parts.extend([
                "📈 MOMENTUM SIGNAL:",
                f"12-Month Return: {momentum_return:.2%}",
                "This stock has shown strong momentum and is being considered for a momentum strategy.",
                ""
            ])

        # Add earnings if available
        if earnings_summary:
            prompt_parts.extend([
                earnings_summary,
                ""
            ])

        # Add analyst data if available
        if analyst_summary:
            prompt_parts.extend([
                analyst_summary,
                ""
            ])

        # Add news
        prompt_parts.extend([
            "📰 RECENT NEWS:",
            news_summary if news_summary else "No recent news available.",
            ""
        ])

        # Analysis instructions
        prompt_parts.extend([
            f"QUESTION: What is your outlook for {symbol} over the next {forecast_days} trading days (~1 month)?",
            "",
            "ANALYSIS FRAMEWORK:",
            "Consider these factors in order of importance:",
            "1. Earnings trends and growth trajectory",
            "2. Analyst consensus and price target implications",
            "3. Recent news sentiment and catalysts",
            "4. Momentum sustainability given the fundamental picture",
            "",
            "Please provide:",
            "1. ANALYSIS: A concise analysis (3-5 sentences) covering:",
            "   - Key fundamental strengths or weaknesses",
            "   - Most important recent developments",
            "   - Your assessment of momentum continuation probability",
            "",
            "2. SCORE: A numerical score from 0 to 1 where:",
            "   - 0.0-0.3 = Bearish (expect underperformance or reversal)",
            "   - 0.4-0.6 = Neutral (mixed signals)",
            "   - 0.7-0.9 = Bullish (expect continued outperformance)",
            "   - 0.9-1.0 = Very Bullish (strong conviction for acceleration)",
            "",
            "Format your response EXACTLY as:",
            "ANALYSIS: [Your 3-5 sentence analysis here]",
            "",
            "SCORE: [number between 0 and 1]"
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def classify_news_importance(title: str, summary: str) -> tuple[str, int]:
        """
        Classify news importance based on keywords.

        Args:
            title: News title
            summary: News summary

        Returns:
            Tuple of (category, priority) where priority is 1 (high) to 3 (low)
        """
        text = (title + " " + summary).lower()

        # High priority: Earnings and major announcements
        high_priority_keywords = [
            'earnings', 'revenue', 'profit', 'eps', 'guidance', 'outlook',
            'quarterly results', 'annual results', 'beats estimates', 'misses estimates',
            'acquisition', 'merger', 'buyback', 'dividend', 'split',
            'fda approval', 'regulatory approval', 'product launch',
            'ceo', 'executive', 'leadership change'
        ]

        # Medium priority: Business developments
        medium_priority_keywords = [
            'partnership', 'contract', 'deal', 'agreement', 'expansion',
            'new product', 'innovation', 'technology', 'patent',
            'market share', 'sales', 'growth', 'investment'
        ]

        # Check for high priority
        for keyword in high_priority_keywords:
            if keyword in text:
                if any(word in text for word in ['earnings', 'revenue', 'profit', 'eps']):
                    return ('EARNINGS', 1)
                elif any(word in text for word in ['acquisition', 'merger']):
                    return ('M&A', 1)
                elif any(word in text for word in ['fda', 'regulatory', 'approval']):
                    return ('REGULATORY', 1)
                else:
                    return ('MAJOR_ANNOUNCEMENT', 1)

        # Check for medium priority
        for keyword in medium_priority_keywords:
            if keyword in text:
                return ('BUSINESS_UPDATE', 2)

        # Default: General news
        return ('GENERAL', 3)

    @staticmethod
    def format_news_for_prompt(
        news_articles,
        max_articles: int = 20,
        max_chars: int = 3000,
        prioritize_important: bool = True
    ) -> str:
        """
        Format news articles for inclusion in prompt with quality scoring.

        Args:
            news_articles: List of news dicts or DataFrame with 'title', 'published', 'summary'
            max_articles: Maximum number of articles to include (increased from 10)
            max_chars: Maximum total characters (increased from 2000)
            prioritize_important: Whether to prioritize high-impact news

        Returns:
            Formatted news summary string
        """
        # Handle DataFrame or empty input
        if news_articles is None:
            return "No recent news available."

        # Convert DataFrame to list of dicts
        import pandas as pd
        if isinstance(news_articles, pd.DataFrame):
            if news_articles.empty:
                return "No recent news available."
            articles = news_articles.to_dict('records')
        elif isinstance(news_articles, list):
            if not news_articles:
                return "No recent news available."
            articles = news_articles
        else:
            return "No recent news available."

        # Classify and prioritize articles
        if prioritize_important:
            articles_with_priority = []
            for article in articles:
                title = article.get('title', '')
                summary = article.get('summary', '')
                category, priority = PromptTemplate.classify_news_importance(title, summary)
                articles_with_priority.append({
                    **article,
                    'category': category,
                    'priority': priority
                })

            # Sort by priority (1 = highest), then by date
            articles_with_priority.sort(key=lambda x: (x['priority'], x.get('published', '')), reverse=True)
            articles = articles_with_priority[:max_articles]
        else:
            articles = articles[:max_articles]

        # Format articles with categories
        summary_parts = []
        total_chars = 0
        categories_seen = set()

        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            published = article.get('published', '')
            summary = article.get('summary', '')
            category = article.get('category', 'GENERAL')

            # Add category marker for important news
            if category != 'GENERAL' and category not in categories_seen:
                category_emoji = {
                    'EARNINGS': '📊',
                    'M&A': '🤝',
                    'REGULATORY': '⚖️',
                    'MAJOR_ANNOUNCEMENT': '📢',
                    'BUSINESS_UPDATE': '💼'
                }.get(category, '📰')
                category_marker = f" {category_emoji}"
                categories_seen.add(category)
            else:
                category_marker = ""

            # Format article
            article_text = f"{i}.{category_marker} {title}"
            if published:
                article_text += f" ({published})"
            if summary:
                # Truncate long summaries but keep more for important news
                max_summary_len = 300 if article.get('priority', 3) <= 2 else 200
                summary_short = summary[:max_summary_len] + "..." if len(summary) > max_summary_len else summary
                article_text += f"\n   {summary_short}"

            # Check character limit
            if total_chars + len(article_text) > max_chars:
                break

            summary_parts.append(article_text)
            total_chars += len(article_text)

        if not summary_parts:
            return "No recent news available."

        return "\n\n".join(summary_parts)

    @staticmethod
    def format_earnings_for_prompt(earnings: Optional[Dict]) -> str:
        """
        Format earnings data for inclusion in LLM prompt.

        Args:
            earnings: Earnings dictionary from EarningsDataFetcher

        Returns:
            Formatted earnings summary string
        """
        if earnings is None:
            return "No earnings data available."

        parts = []

        # Latest quarter info
        quarter_date = earnings.get('latest_quarter_date')
        if quarter_date:
            parts.append(f"📊 LATEST EARNINGS ({quarter_date}):")
        else:
            parts.append("📊 LATEST EARNINGS:")

        # EPS and Revenue
        latest_eps = earnings.get('latest_eps')
        latest_revenue = earnings.get('latest_revenue')

        if latest_eps is not None:
            parts.append(f"  • EPS: ${latest_eps:.2f}")
        if latest_revenue is not None:
            parts.append(f"  • Revenue: ${latest_revenue:,.0f}")

        # Growth metrics (most important)
        yoy_eps = earnings.get('yoy_eps_growth')
        yoy_rev = earnings.get('yoy_revenue_growth')
        qoq = earnings.get('qoq_growth')

        if yoy_eps is not None or yoy_rev is not None or qoq is not None:
            parts.append("\n📈 GROWTH:")
            if yoy_eps is not None:
                growth_emoji = "🟢" if yoy_eps > 0.15 else "🟡" if yoy_eps > 0 else "🔴"
                parts.append(f"  • YoY EPS Growth: {growth_emoji} {yoy_eps*100:+.1f}%")
            if yoy_rev is not None:
                growth_emoji = "🟢" if yoy_rev > 0.15 else "🟡" if yoy_rev > 0 else "🔴"
                parts.append(f"  • YoY Revenue Growth: {growth_emoji} {yoy_rev*100:+.1f}%")
            if qoq is not None:
                parts.append(f"  • QoQ EPS Growth: {qoq*100:+.1f}%")

        # Profitability metrics
        profit_margin = earnings.get('profit_margin')
        operating_margin = earnings.get('operating_margin')
        gross_margin = earnings.get('gross_margin')

        if any(x is not None for x in [profit_margin, operating_margin, gross_margin]):
            parts.append("\n💰 PROFITABILITY:")
            if profit_margin is not None:
                parts.append(f"  • Profit Margin: {profit_margin*100:.1f}%")
            if operating_margin is not None:
                parts.append(f"  • Operating Margin: {operating_margin*100:.1f}%")
            if gross_margin is not None:
                parts.append(f"  • Gross Margin: {gross_margin*100:.1f}%")

        # Financial health
        debt_to_equity = earnings.get('debt_to_equity')
        roe = earnings.get('roe')
        roa = earnings.get('roa')

        if any(x is not None for x in [debt_to_equity, roe, roa]):
            parts.append("\n🏦 FINANCIAL HEALTH:")
            if debt_to_equity is not None:
                health_emoji = "🟢" if debt_to_equity < 1.0 else "🟡" if debt_to_equity < 2.0 else "🔴"
                parts.append(f"  • Debt/Equity: {health_emoji} {debt_to_equity:.2f}")
            if roe is not None:
                parts.append(f"  • ROE: {roe*100:.1f}%")
            if roa is not None:
                parts.append(f"  • ROA: {roa*100:.1f}%")

        # Forward estimates
        forward_eps = earnings.get('forward_eps')
        trailing_eps = earnings.get('trailing_eps')

        if forward_eps is not None or trailing_eps is not None:
            parts.append("\n📍 ESTIMATES:")
            if forward_eps is not None:
                parts.append(f"  • Forward EPS: ${forward_eps:.2f}")
            if trailing_eps is not None:
                parts.append(f"  • Trailing EPS: ${trailing_eps:.2f}")

        if not parts:
            return "No earnings data available."

        return "\n".join(parts)

    @staticmethod
    def format_analyst_data_for_prompt(analyst_data: Optional[Dict]) -> str:
        """
        Format analyst data for inclusion in LLM prompt.

        Args:
            analyst_data: Analyst dictionary from AnalystDataFetcher

        Returns:
            Formatted analyst summary string
        """
        if analyst_data is None:
            return "No analyst data available."

        parts = []
        parts.append("🎯 ANALYST RATINGS & TARGETS:")

        # Recommendation
        recommendation = analyst_data.get('recommendation')
        rec_mean = analyst_data.get('recommendation_mean')
        num_analysts = analyst_data.get('number_of_analysts')

        if recommendation or rec_mean:
            rec_text = recommendation.upper() if recommendation else "N/A"

            # Add emoji based on recommendation
            if rec_mean:
                if rec_mean <= 1.5:
                    rec_emoji = "🟢"  # Strong Buy
                elif rec_mean <= 2.5:
                    rec_emoji = "🟡"  # Buy/Hold
                elif rec_mean <= 3.5:
                    rec_emoji = "🟠"  # Hold
                else:
                    rec_emoji = "🔴"  # Sell
            else:
                rec_emoji = "⚪"

            parts.append(f"  • Consensus: {rec_emoji} {rec_text}")

            if num_analysts:
                parts.append(f"  • Number of Analysts: {num_analysts}")

        # Price targets
        current_price = analyst_data.get('current_price')
        target_mean = analyst_data.get('target_mean_price')
        target_high = analyst_data.get('target_high_price')
        target_low = analyst_data.get('target_low_price')
        upside = analyst_data.get('upside_potential')

        if target_mean and current_price:
            parts.append("\n📊 PRICE TARGETS:")
            parts.append(f"  • Current Price: ${current_price:.2f}")
            parts.append(f"  • Analyst Target: ${target_mean:.2f}")

            if target_high and target_low:
                parts.append(f"  • Range: ${target_low:.2f} - ${target_high:.2f}")

            if upside is not None:
                upside_emoji = "🟢" if upside > 0.15 else "🟡" if upside > 0 else "🔴"
                parts.append(f"  • Upside Potential: {upside_emoji} {upside*100:+.1f}%")

        # Earnings estimates
        forward_eps = analyst_data.get('forward_eps')
        forward_pe = analyst_data.get('forward_pe')

        if forward_eps or forward_pe:
            parts.append("\n📈 EARNINGS ESTIMATES:")
            if forward_eps:
                parts.append(f"  • Forward EPS: ${forward_eps:.2f}")
            if forward_pe:
                parts.append(f"  • Forward P/E: {forward_pe:.1f}x")

        # Growth estimates
        earnings_growth = analyst_data.get('earnings_growth')
        revenue_growth = analyst_data.get('revenue_growth')

        if earnings_growth is not None or revenue_growth is not None:
            parts.append("\n💹 GROWTH ESTIMATES:")
            if earnings_growth is not None:
                growth_emoji = "🟢" if earnings_growth > 0.15 else "🟡" if earnings_growth > 0 else "🔴"
                parts.append(f"  • Earnings Growth: {growth_emoji} {earnings_growth*100:+.1f}%")
            if revenue_growth is not None:
                growth_emoji = "🟢" if revenue_growth > 0.15 else "🟡" if revenue_growth > 0 else "🔴"
                parts.append(f"  • Revenue Growth: {growth_emoji} {revenue_growth*100:+.1f}%")

        # Recent upgrades/downgrades
        upgrades = analyst_data.get('recent_upgrades')
        downgrades = analyst_data.get('recent_downgrades')

        if upgrades is not None and downgrades is not None:
            parts.append("\n⬆️⬇️ RECENT CHANGES (90 days):")
            parts.append(f"  • Upgrades: {upgrades}")
            parts.append(f"  • Downgrades: {downgrades}")

            if upgrades > downgrades and upgrades > 0:
                parts.append(f"  • Trend: 🟢 Positive ({upgrades - downgrades} net upgrades)")
            elif downgrades > upgrades and downgrades > 0:
                parts.append(f"  • Trend: 🔴 Negative ({downgrades - upgrades} net downgrades)")
            else:
                parts.append(f"  • Trend: ⚪ Neutral")

        if not parts or len(parts) == 1:
            return "No analyst data available."

        return "\n".join(parts)

    @staticmethod
    def get_system_prompt() -> str:
        """
        Get system prompt for LLM initialization.

        Returns:
            System prompt string
        """
        return (
            "You are a quantitative financial analyst specializing in momentum investing. "
            "You provide objective, data-driven assessments of stocks based on news and technical indicators. "
            "You are precise, analytical, and focus on near-term price movements."
        )


def main():
    """Test prompt templates."""
    from loguru import logger

    # Sample data
    symbol = "AAPL"
    momentum = 0.452
    news = """
    1. Apple Reports Record Q4 Revenue (Nov 2, 2024)
       Apple Inc. announced quarterly revenue of $89.5 billion, beating analyst estimates.
       iPhone sales grew 6% year-over-year driven by strong demand for iPhone 15 Pro models.

    2. Apple Services Segment Hits New High (Nov 1, 2024)
       Services revenue reached $22.3 billion, up 16% from last year, marking another record quarter.
    """

    logger.info("Testing Prompt Templates")
    logger.info("="*70)

    # Test basic prompt
    logger.info("\n1. BASIC PROMPT:")
    basic = PromptTemplate.basic_prompt(symbol, news, momentum)
    print(basic)

    # Test advanced prompt
    logger.info("\n\n2. ADVANCED PROMPT:")
    advanced = PromptTemplate.advanced_prompt(
        symbol, news, momentum,
        company_name="Apple Inc.",
        sector="Technology"
    )
    print(advanced)

    # Test research prompt
    logger.info("\n\n3. RESEARCH PROMPT:")
    research = PromptTemplate.research_prompt(symbol, news, momentum)
    print(research)

    # Test news formatting
    logger.info("\n\n4. NEWS FORMATTING:")
    news_articles = [
        {
            'title': 'Apple hits new high',
            'published': '2024-11-02',
            'summary': 'Apple stock reaches record levels on strong earnings.'
        },
        {
            'title': 'iPhone demand surges',
            'published': '2024-11-01',
            'summary': 'iPhone 15 Pro models drive sales growth in Q4.'
        }
    ]
    formatted = PromptTemplate.format_news_for_prompt(news_articles)
    print(formatted)


if __name__ == "__main__":
    main()

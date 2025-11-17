"""
LLM Risk Index Scorer

Analyzes news sentiment to detect risk signals for individual stocks.
Complements the portfolio-level volatility protection with stock-level risk assessment.
"""

import pandas as pd
from typing import Dict, List, Optional
from loguru import logger
from openai import OpenAI
import os


class LLMRiskScorer:
    """
    Scores individual stocks for risk based on recent news sentiment.

    Risk Score: 0.0 (safe) to 1.0 (high risk)

    Risk Signals:
    - Negative earnings surprises
    - Regulatory issues
    - Management changes
    - Competitive threats
    - Financial distress
    - Legal problems
    """

    RISK_ASSESSMENT_PROMPT = """You are a financial risk analyst. Analyze the following recent news for {symbol} and assess risk signals.

Recent News:
{news}

Evaluate the stock on these risk factors:

1. **Financial Risk** (earnings misses, revenue decline, debt issues)
2. **Operational Risk** (supply chain, production, management changes)
3. **Regulatory Risk** (investigations, lawsuits, compliance issues)
4. **Competitive Risk** (market share loss, new competitors)
5. **Market Risk** (sector headwinds, macro challenges)

For each risk factor, rate as: LOW, MEDIUM, or HIGH

Then provide:
- Overall Risk Score: 0.0 (very safe) to 1.0 (very risky)
- Key Risk: The main concern (if any)
- Recommendation: HOLD (safe), REDUCE (moderate risk), or SELL (high risk)

Respond in JSON format:
{{
    "financial_risk": "LOW/MEDIUM/HIGH",
    "operational_risk": "LOW/MEDIUM/HIGH",
    "regulatory_risk": "LOW/MEDIUM/HIGH",
    "competitive_risk": "LOW/MEDIUM/HIGH",
    "market_risk": "LOW/MEDIUM/HIGH",
    "overall_risk_score": 0.0-1.0,
    "key_risk": "Brief description or 'None'",
    "recommendation": "HOLD/REDUCE/SELL",
    "reasoning": "Brief explanation"
}}

If news is insufficient or mostly positive, score should be low (0.0-0.3).
"""

    def __init__(self, model: str = "gpt-4o-mini", api_keys_path: str = "config/api_keys.yaml"):
        """
        Initialize LLM risk scorer.

        Args:
            model: OpenAI model to use for risk assessment
            api_keys_path: Path to API keys configuration file
        """
        self.model = model

        # Load API key - try multiple sources
        api_key = None

        # 1. Try Streamlit secrets (for deployed apps)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'openai' in st.secrets:
                api_key = st.secrets['openai'].get('api_key')
                logger.info("Using OpenAI API key from Streamlit secrets")
        except:
            pass

        # 2. Try environment variable
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                logger.info("Using OpenAI API key from environment variable")

        # 3. Try config file
        if not api_key:
            import yaml
            try:
                with open(api_keys_path, 'r') as f:
                    api_keys = yaml.safe_load(f)
                api_key = api_keys.get('openai', {}).get('api_key')
                if api_key:
                    logger.info("Using OpenAI API key from config file")
            except FileNotFoundError:
                pass

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set it in:\n"
                "  1. Streamlit Cloud: Add to secrets as [openai] api_key = \"sk-...\"\n"
                "  2. Environment: export OPENAI_API_KEY='sk-...'\n"
                "  3. Config file: config/api_keys.yaml"
            )

        self.client = OpenAI(api_key=api_key)
        logger.info(f"LLMRiskScorer initialized with model: {model}")

    def score_stock_risk(
        self,
        symbol: str,
        news_articles: List[str],
        max_articles: int = 5,
        return_prompt: bool = False
    ) -> Dict:
        """
        Score risk for a single stock based on recent news.

        Args:
            symbol: Stock ticker symbol
            news_articles: List of recent news article texts
            max_articles: Maximum number of articles to analyze

        Returns:
            Dictionary with risk scores and assessment
        """
        if not news_articles or len(news_articles) == 0:
            # No news - assume neutral risk
            result = {
                'symbol': symbol,
                'overall_risk_score': 0.5,
                'key_risk': 'Insufficient news data',
                'recommendation': 'HOLD',
                'financial_risk': 'MEDIUM',
                'operational_risk': 'MEDIUM',
                'regulatory_risk': 'MEDIUM',
                'competitive_risk': 'MEDIUM',
                'market_risk': 'MEDIUM',
                'reasoning': 'No recent news available for analysis'
            }

            # Include placeholder prompt if requested
            if return_prompt:
                result['risk_prompt'] = f"""You are a financial risk analyst. Analyze the following recent news for {symbol} and assess risk signals.

Recent News:
No recent news available.

Note: Risk assessment defaulted to neutral (0.5) due to insufficient data."""

            return result

        # Limit number of articles
        news_sample = news_articles[:max_articles]
        news_text = "\n\n".join([f"Article {i+1}: {article}" for i, article in enumerate(news_sample)])

        prompt = self.RISK_ASSESSMENT_PROMPT.format(
            symbol=symbol,
            news=news_text
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial risk analyst providing objective risk assessments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            result['symbol'] = symbol

            logger.info(f"{symbol}: Risk Score = {result['overall_risk_score']:.2f}, Recommendation = {result['recommendation']}")

            if return_prompt:
                result['risk_prompt'] = prompt

            return result

        except Exception as e:
            logger.error(f"Error scoring risk for {symbol}: {e}")
            result = {
                'symbol': symbol,
                'overall_risk_score': 0.5,
                'key_risk': f'Error: {str(e)}',
                'recommendation': 'HOLD',
                'financial_risk': 'MEDIUM',
                'operational_risk': 'MEDIUM',
                'regulatory_risk': 'MEDIUM',
                'competitive_risk': 'MEDIUM',
                'market_risk': 'MEDIUM',
                'reasoning': 'Error during analysis'
            }

            # Include prompt even for errors if requested
            if return_prompt:
                result['risk_prompt'] = prompt  # Use the prompt that was generated before the error

            return result

    def score_portfolio_risks(
        self,
        portfolio: pd.DataFrame,
        news_data: Dict[str, List[str]],
        show_progress: bool = True,
        store_prompts: bool = False,
        prompt_store = None
    ) -> pd.DataFrame:
        """
        Score risk for all stocks in a portfolio.

        Args:
            portfolio: Portfolio DataFrame with 'symbol' column
            news_data: Dictionary mapping symbol -> list of news articles
            show_progress: Whether to show progress

        Returns:
            Portfolio DataFrame with risk scores added
        """
        logger.info(f"Scoring risk for {len(portfolio)} stocks...")

        # Initialize prompt store if needed
        if store_prompts and prompt_store is None:
            from .prompt_store import get_prompt_store
            prompt_store = get_prompt_store()

        risk_scores = []

        for idx, row in portfolio.iterrows():
            symbol = row['symbol']

            if show_progress:
                logger.info(f"Analyzing risk for {symbol} ({idx+1}/{len(portfolio)})")

            # Get news for this stock
            news = news_data.get(symbol, [])

            # Score risk (with prompt return if storing)
            risk_assessment = self.score_stock_risk(symbol, news, return_prompt=store_prompts)

            # Store prompt if requested
            if store_prompts and prompt_store and 'risk_prompt' in risk_assessment:
                prompt_store.store_prompt(
                    symbol=symbol,
                    prompt=risk_assessment['risk_prompt'],
                    prompt_type='risk_scoring',
                    metadata={
                        'model': self.model,
                        'risk_score': risk_assessment['overall_risk_score']
                    }
                )

            risk_scores.append(risk_assessment)

        # Add risk scores to portfolio
        portfolio_with_risk = portfolio.copy()
        portfolio_with_risk['risk_score'] = [r['overall_risk_score'] for r in risk_scores]
        portfolio_with_risk['risk_recommendation'] = [r['recommendation'] for r in risk_scores]
        portfolio_with_risk['key_risk'] = [r['key_risk'] for r in risk_scores]

        # Add individual risk factors (optional, for detailed analysis)
        portfolio_with_risk['financial_risk'] = [r['financial_risk'] for r in risk_scores]
        portfolio_with_risk['operational_risk'] = [r['operational_risk'] for r in risk_scores]
        portfolio_with_risk['regulatory_risk'] = [r['regulatory_risk'] for r in risk_scores]

        logger.info(f"Risk scoring complete. Average risk: {portfolio_with_risk['risk_score'].mean():.2f}")

        # Show high-risk stocks
        high_risk = portfolio_with_risk[portfolio_with_risk['risk_score'] > 0.7]
        if len(high_risk) > 0:
            logger.warning(f"⚠️  {len(high_risk)} high-risk stocks detected:")
            for _, stock in high_risk.iterrows():
                logger.warning(f"  {stock['symbol']}: {stock['risk_score']:.2f} - {stock['key_risk']}")

        return portfolio_with_risk

    def apply_risk_based_adjustment(
        self,
        portfolio: pd.DataFrame,
        risk_threshold: float = 0.7,
        reduction_factor: float = 0.5
    ) -> pd.DataFrame:
        """
        Reduce weights for high-risk stocks.

        Args:
            portfolio: Portfolio with risk_score column
            risk_threshold: Risk score above which to reduce weights
            reduction_factor: How much to reduce (0.5 = reduce to 50%)

        Returns:
            Portfolio with adjusted weights
        """
        if 'risk_score' not in portfolio.columns:
            logger.warning("No risk scores found, cannot apply risk adjustment")
            return portfolio

        adjusted = portfolio.copy()

        # Identify high-risk stocks
        high_risk_mask = adjusted['risk_score'] > risk_threshold
        n_high_risk = high_risk_mask.sum()

        if n_high_risk == 0:
            logger.info("No high-risk stocks detected, no adjustment needed")
            return adjusted

        logger.info(f"Reducing weights for {n_high_risk} high-risk stocks (risk > {risk_threshold})")

        # Store original weights
        adjusted['original_weight_before_risk_adj'] = adjusted['weight']

        # Reduce high-risk weights
        adjusted.loc[high_risk_mask, 'weight'] = adjusted.loc[high_risk_mask, 'weight'] * reduction_factor

        # Renormalize to sum to 1
        adjusted['weight'] = adjusted['weight'] / adjusted['weight'].sum()

        # Log changes
        for _, stock in adjusted[high_risk_mask].iterrows():
            old_weight = stock['original_weight_before_risk_adj']
            new_weight = stock['weight']
            logger.info(
                f"  {stock['symbol']}: "
                f"{old_weight:.2%} → {new_weight:.2%} "
                f"(risk: {stock['risk_score']:.2f})"
            )

        return adjusted


def main():
    """Test LLM risk scorer."""
    logger.info("Testing LLM Risk Scorer")
    logger.info("="*70)

    # Example news for testing
    test_news = {
        'AAPL': [
            "Apple reports strong quarterly earnings, beating analyst expectations.",
            "iPhone sales continue to grow in emerging markets.",
            "Apple announces new AI features for upcoming iOS release."
        ],
        'NVDA': [
            "NVIDIA facing supply chain constraints for latest GPUs.",
            "Competition intensifies as AMD launches rival AI chips.",
            "NVIDIA CEO warns of potential export restrictions to China."
        ],
        'TSLA': [
            "Tesla recalls 2 million vehicles over autopilot safety concerns.",
            "SEC investigates Tesla CEO's recent public statements.",
            "Tesla stock drops 15% on disappointing delivery numbers."
        ]
    }

    # Create test portfolio
    test_portfolio = pd.DataFrame({
        'symbol': ['AAPL', 'NVDA', 'TSLA'],
        'weight': [0.33, 0.33, 0.34],
        'momentum_return': [0.25, 0.45, 0.15]
    })

    # Initialize scorer
    scorer = LLMRiskScorer()

    # Score portfolio
    portfolio_with_risk = scorer.score_portfolio_risks(
        test_portfolio,
        test_news,
        show_progress=True
    )

    print("\n" + "="*70)
    print("PORTFOLIO WITH RISK SCORES")
    print("="*70 + "\n")

    display_cols = ['symbol', 'weight', 'risk_score', 'risk_recommendation', 'key_risk']
    print(portfolio_with_risk[display_cols].to_string(index=False))

    # Test risk-based adjustment
    print("\n" + "="*70)
    print("RISK-BASED WEIGHT ADJUSTMENT")
    print("="*70 + "\n")

    adjusted_portfolio = scorer.apply_risk_based_adjustment(
        portfolio_with_risk,
        risk_threshold=0.6,
        reduction_factor=0.5
    )

    print("\nAdjusted weights:")
    display_cols = ['symbol', 'original_weight_before_risk_adj', 'weight', 'risk_score']
    print(adjusted_portfolio[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()

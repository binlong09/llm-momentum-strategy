"""
LLM Stock Scorer
Uses LLM to score stocks based on news and momentum signals.
"""

import os
import time
import re
import numpy as np
from typing import Dict, List, Optional, Tuple
from loguru import logger
from openai import OpenAI
import yaml

from .prompts import PromptTemplate


class LLMScorer:
    """
    Scores stocks using LLM based on news and momentum.

    Features:
    - OpenAI API integration
    - Automatic retry with exponential backoff
    - Score normalization to [-1, 1] range
    - Batch processing support
    - Rate limiting
    """

    def __init__(
        self,
        config_path: str = "config/config.yaml",
        api_keys_path: str = "config/api_keys.yaml",
        model: Optional[str] = None
    ):
        """
        Initialize LLM scorer.

        Args:
            config_path: Path to configuration file
            api_keys_path: Path to API keys file
            model: Optional model override (e.g., 'gpt-4o', 'gpt-4-turbo')
                   If None, uses model from api_keys.yaml
        """
        self.config = self._load_config(config_path)
        self.api_keys = self._load_config(api_keys_path)

        # Extract LLM config
        llm_config = self.config.get('strategy', {}).get('llm', {})
        self.prompt_type = llm_config.get('prompt_type', 'basic')
        self.forecast_days = llm_config.get('forecast_horizon_days', 21)
        self.max_retries = llm_config.get('max_retries', 3)
        self.timeout = llm_config.get('timeout_seconds', 30)
        self.score_range = llm_config.get('score_range', [0, 1])

        # Initialize OpenAI client
        # Try multiple sources for API key: Streamlit secrets, env vars, then config file
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
            api_key = self.api_keys.get('openai', {}).get('api_key')
            if api_key:
                logger.info("Using OpenAI API key from config file")

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set it in:\n"
                "  1. Streamlit Cloud: Add to secrets as [openai] api_key = \"sk-...\"\n"
                "  2. Environment: export OPENAI_API_KEY='sk-...'\n"
                "  3. Config file: config/api_keys.yaml"
            )

        self.client = OpenAI(api_key=api_key)

        # Use provided model or default from config
        self.model = model if model is not None else self.api_keys.get('openai', {}).get('model', 'gpt-4o-mini')

        # Prompt template
        self.prompt_template = PromptTemplate()

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        logger.info(
            f"LLMScorer initialized: model={self.model}, "
            f"prompt_type={self.prompt_type}, forecast_days={self.forecast_days}"
        )

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config from {path}: {e}")
            return {}

    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        Call LLM API with retry logic.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            LLM response text or None on failure
        """
        if system_prompt is None:
            system_prompt = self.prompt_template.get_system_prompt()

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self._rate_limit()

                # Make API call
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )

                # Extract response
                result = response.choices[0].message.content.strip()
                return result

            except Exception as e:
                logger.warning(f"LLM API call failed (attempt {attempt+1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1.0
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for LLM call")
                    return None

        return None

    def _parse_score(self, response: str) -> Optional[float]:
        """
        Parse numerical score from LLM response.

        Args:
            response: LLM response text

        Returns:
            Parsed score or None
        """
        if not response:
            return None

        # Try to extract number from response
        # Look for patterns like "0.75", "SCORE: 0.8", etc.
        patterns = [
            r'(?:SCORE:?\s*)?(\d+\.?\d*)',  # SCORE: 0.75 or just 0.75
            r'(\d+\.?\d*)\s*(?:out of 1)?',  # 0.75 out of 1
            r'(?:rating|score).*?(\d+\.?\d*)',  # rating of 0.75
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))

                    # Handle scores > 1 (e.g., "8 out of 10")
                    if score > 1 and score <= 10:
                        score = score / 10.0

                    # Validate range
                    if 0 <= score <= 1:
                        return score

                except (ValueError, IndexError):
                    continue

        logger.warning(f"Could not parse score from response: {response[:100]}")
        return None

    def normalize_score(self, raw_score: float) -> float:
        """
        Normalize score from [0, 1] to [-1, 1] range.

        Args:
            raw_score: Raw LLM score (0-1)

        Returns:
            Normalized score (-1 to 1)
        """
        # Map [0, 1] to [-1, 1]
        # 0 -> -1 (very negative)
        # 0.5 -> 0 (neutral)
        # 1 -> 1 (very positive)
        normalized = (raw_score - 0.5) * 2
        return normalized

    def _parse_research_response(self, response: str) -> Optional[Tuple[str, float]]:
        """
        Parse research mode response to extract analysis and score.

        Args:
            response: LLM response with ANALYSIS and SCORE

        Returns:
            Tuple of (analysis_text, score) or None if parsing fails
        """
        if not response:
            return None

        analysis = None
        score = None

        # Extract ANALYSIS section
        analysis_match = re.search(r'ANALYSIS:\s*(.+?)(?=\n\s*SCORE:|$)', response, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            analysis = analysis_match.group(1).strip()

        # Extract SCORE section
        score_match = re.search(r'SCORE:\s*(\d+\.?\d*)', response, re.IGNORECASE)
        if score_match:
            try:
                score_val = float(score_match.group(1))
                if 0 <= score_val <= 1:
                    score = score_val
            except ValueError:
                pass

        # Fallback: try to find just a number if SCORE label missing
        if score is None:
            score = self._parse_score(response)

        if analysis and score is not None:
            return (analysis, score)

        logger.warning(f"Could not parse research response. Analysis: {analysis is not None}, Score: {score is not None}")
        return None

    def score_stock_with_research(
        self,
        symbol: str,
        news_summary: str,
        momentum_return: Optional[float] = None,
        earnings_data: Optional[Dict] = None,
        analyst_data: Optional[Dict] = None,
        return_prompt: bool = False
    ) -> Optional[Tuple[float, float, str]]:
        """
        Score a stock using research mode (returns analysis + score).

        Args:
            symbol: Stock ticker
            news_summary: Recent news summary
            momentum_return: 12-month momentum return
            earnings_data: Optional earnings data
            analyst_data: Optional analyst data
            return_prompt: If True, also return the prompt

        Returns:
            Tuple of (raw_score, normalized_score, analysis_text)
            If return_prompt=True: (raw_score, normalized_score, analysis_text, prompt)
        """
        # Format data
        earnings_summary = None
        if earnings_data:
            earnings_summary = self.prompt_template.format_earnings_for_prompt(earnings_data)

        analyst_summary = None
        if analyst_data:
            analyst_summary = self.prompt_template.format_analyst_data_for_prompt(analyst_data)

        # Generate research prompt
        prompt = self.prompt_template.research_prompt(
            symbol=symbol,
            news_summary=news_summary,
            momentum_return=momentum_return,
            earnings_summary=earnings_summary,
            analyst_summary=analyst_summary,
            forecast_days=self.forecast_days
        )

        # Call LLM with higher max_tokens for analysis
        logger.debug(f"Scoring {symbol} with research mode...")

        # Store original timeout and increase for research mode
        original_timeout = self.timeout
        self.timeout = 60  # Longer timeout for research mode

        response = self._call_llm(prompt, temperature=0.3, max_tokens=500)

        # Restore original timeout
        self.timeout = original_timeout

        if response is None:
            logger.error(f"Failed to get LLM response for {symbol}")
            return None

        # Parse analysis and score
        parsed = self._parse_research_response(response)

        if parsed is None:
            logger.error(f"Failed to parse research response for {symbol}")
            return None

        analysis, raw_score = parsed
        normalized_score = self.normalize_score(raw_score)

        logger.debug(
            f"{symbol}: raw_score={raw_score:.3f}, "
            f"normalized_score={normalized_score:.3f}, "
            f"analysis_length={len(analysis)} chars"
        )

        if return_prompt:
            return (raw_score, normalized_score, analysis, prompt)
        else:
            return (raw_score, normalized_score, analysis)

    def score_stock(
        self,
        symbol: str,
        news_summary: str,
        momentum_return: Optional[float] = None,
        company_info: Optional[Dict] = None,
        earnings_data: Optional[Dict] = None,
        analyst_data: Optional[Dict] = None,
        return_prompt: bool = False
    ) -> Optional[Tuple[float, float]]:
        """
        Score a single stock using LLM.

        Args:
            symbol: Stock ticker
            news_summary: Recent news summary
            momentum_return: 12-month momentum return
            company_info: Optional dict with 'name' and 'sector'
            earnings_data: Optional earnings data dict (from EarningsDataFetcher)
            analyst_data: Optional analyst data dict (from AnalystDataFetcher)
            return_prompt: If True, return (raw_score, normalized_score, prompt)

        Returns:
            Tuple of (raw_score, normalized_score) or None on failure
            If return_prompt=True: (raw_score, normalized_score, prompt)
        """
        # Format earnings data if provided
        earnings_summary = None
        if earnings_data:
            earnings_summary = self.prompt_template.format_earnings_for_prompt(earnings_data)

        # Format analyst data if provided
        analyst_summary = None
        if analyst_data:
            analyst_summary = self.prompt_template.format_analyst_data_for_prompt(analyst_data)

        # Generate prompt based on type
        if self.prompt_type == 'advanced' and company_info:
            prompt = self.prompt_template.advanced_prompt(
                symbol=symbol,
                news_summary=news_summary,
                momentum_return=momentum_return,
                company_name=company_info.get('name'),
                sector=company_info.get('sector'),
                earnings_summary=earnings_summary,
                analyst_summary=analyst_summary,
                forecast_days=self.forecast_days
            )
        else:
            # Basic prompt now also supports earnings and analyst data
            prompt = self.prompt_template.basic_prompt(
                symbol=symbol,
                news_summary=news_summary,
                momentum_return=momentum_return,
                earnings_summary=earnings_summary,
                analyst_summary=analyst_summary,
                forecast_days=self.forecast_days
            )

        # Call LLM
        logger.debug(f"Scoring {symbol} with LLM...")
        response = self._call_llm(prompt)

        if response is None:
            logger.error(f"Failed to get LLM response for {symbol}")
            return None

        # Parse score
        raw_score = self._parse_score(response)

        if raw_score is None:
            logger.error(f"Failed to parse score for {symbol} from: {response[:100]}")
            return None

        # Normalize
        normalized_score = self.normalize_score(raw_score)

        logger.debug(
            f"{symbol}: raw_score={raw_score:.3f}, "
            f"normalized_score={normalized_score:.3f}"
        )

        if return_prompt:
            return (raw_score, normalized_score, prompt)
        else:
            return (raw_score, normalized_score)

    def score_batch(
        self,
        stocks_data: List[Dict],
        show_progress: bool = True
    ) -> Dict[str, Tuple[float, float]]:
        """
        Score multiple stocks in batch.

        Args:
            stocks_data: List of dicts with keys:
                - 'symbol': Stock ticker
                - 'news_summary': News text
                - 'momentum_return': 12-month return
                - 'company_info': Optional company data
                - 'earnings_data': Optional earnings data
                - 'analyst_data': Optional analyst data
            show_progress: Show progress bar

        Returns:
            Dictionary mapping symbol to (raw_score, normalized_score)
        """
        results = {}

        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(stocks_data, desc="Scoring stocks")
            except ImportError:
                iterator = stocks_data
        else:
            iterator = stocks_data

        for stock in iterator:
            symbol = stock['symbol']

            try:
                score_result = self.score_stock(
                    symbol=symbol,
                    news_summary=stock.get('news_summary', ''),
                    momentum_return=stock.get('momentum_return'),
                    company_info=stock.get('company_info'),
                    earnings_data=stock.get('earnings_data'),
                    analyst_data=stock.get('analyst_data')
                )

                if score_result:
                    results[symbol] = score_result
                else:
                    logger.warning(f"Skipping {symbol}: scoring failed")

            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
                continue

        logger.success(f"Successfully scored {len(results)}/{len(stocks_data)} stocks")

        return results

    def get_score_statistics(
        self,
        scores: Dict[str, Tuple[float, float]]
    ) -> Dict:
        """
        Calculate statistics for a batch of scores.

        Args:
            scores: Dictionary of symbol -> (raw, normalized) scores

        Returns:
            Dictionary with statistics
        """
        if not scores:
            return {}

        raw_scores = [s[0] for s in scores.values()]
        normalized_scores = [s[1] for s in scores.values()]

        stats = {
            'count': len(scores),
            'raw_mean': np.mean(raw_scores),
            'raw_std': np.std(raw_scores),
            'raw_min': np.min(raw_scores),
            'raw_max': np.max(raw_scores),
            'normalized_mean': np.mean(normalized_scores),
            'normalized_std': np.std(normalized_scores),
            'normalized_min': np.min(normalized_scores),
            'normalized_max': np.max(normalized_scores)
        }

        return stats


def main():
    """Test LLM scorer."""
    from src.data import DataManager

    logger.info("Testing LLM Scorer")
    logger.info("="*70)

    # Initialize
    scorer = LLMScorer()
    dm = DataManager()

    # Get sample stocks
    test_symbols = ['AAPL', 'MSFT', 'NVDA']

    logger.info(f"\nTesting with {len(test_symbols)} stocks...")

    # Prepare data
    stocks_data = []

    for symbol in test_symbols:
        # Get news
        news_articles = dm.get_news(symbol, lookback_days=5)
        news_summary = PromptTemplate.format_news_for_prompt(news_articles)

        # Get price data for momentum
        price_data = dm.get_prices([symbol], use_cache=True, show_progress=False)
        momentum = None

        if symbol in price_data and price_data[symbol] is not None:
            from src.strategy import MomentumCalculator
            calc = MomentumCalculator()
            momentum = calc.calculate_momentum(price_data[symbol])

        stocks_data.append({
            'symbol': symbol,
            'news_summary': news_summary,
            'momentum_return': momentum,
            'company_info': {'name': symbol, 'sector': 'Technology'}
        })

    # Score stocks
    logger.info("\nScoring stocks...")
    results = scorer.score_batch(stocks_data, show_progress=True)

    # Display results
    logger.info("\n" + "="*70)
    logger.info("RESULTS")
    logger.info("="*70)

    for symbol in test_symbols:
        if symbol in results:
            raw, normalized = results[symbol]
            logger.info(
                f"{symbol}: Raw={raw:.3f} (0-1), "
                f"Normalized={normalized:.3f} (-1 to 1)"
            )
        else:
            logger.warning(f"{symbol}: Scoring failed")

    # Statistics
    stats = scorer.get_score_statistics(results)
    logger.info("\nScore Statistics:")
    logger.info(f"  Count: {stats.get('count', 0)}")
    logger.info(f"  Raw scores: {stats.get('raw_mean', 0):.3f} ± {stats.get('raw_std', 0):.3f}")
    logger.info(f"  Normalized: {stats.get('normalized_mean', 0):.3f} ± {stats.get('normalized_std', 0):.3f}")


if __name__ == "__main__":
    main()

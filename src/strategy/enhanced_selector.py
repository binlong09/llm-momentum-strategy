"""
Enhanced Stock Selector with LLM Re-ranking
Extends baseline momentum selection with LLM-based scoring and re-ranking.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, List, Optional, Tuple
import yaml

from .selector import StockSelector
from src.llm import LLMScorer, PromptTemplate
from src.data import DataManager


class EnhancedSelector(StockSelector):
    """
    Enhanced stock selector with LLM re-ranking.

    Pipeline:
    1. Use baseline momentum selection (top 20%)
    2. Fetch recent news for selected stocks
    3. Score stocks with LLM
    4. Re-rank based on LLM scores
    5. Select final portfolio (top N by LLM score)
    """

    def __init__(self, config_path: str = "config/config.yaml", model: Optional[str] = None):
        """
        Initialize enhanced selector.

        Args:
            config_path: Path to strategy configuration
            model: Optional LLM model override (e.g., 'gpt-4o', 'gpt-4-turbo')
        """
        # Initialize base selector
        super().__init__(config_path)

        # Initialize LLM components
        try:
            self.llm_scorer = LLMScorer(config_path, model=model)
            self.llm_enabled = True
            logger.info(f"LLM scorer initialized successfully with model: {self.llm_scorer.model}")
        except Exception as e:
            logger.warning(f"Failed to initialize LLM scorer: {e}")
            logger.warning("Falling back to baseline momentum selection")
            self.llm_enabled = False

        # Initialize data manager for news
        self.data_manager = DataManager(config_path)

        # Extract LLM config
        llm_config = self.config.get('strategy', {}).get('llm', {})
        self.news_lookback_days = llm_config.get('news_lookback_days', 1)
        self.batch_size = llm_config.get('batch_size', 10)

        # Re-ranking method
        self.rerank_method = 'llm_only'  # 'llm_only', 'combined', 'weighted'

        logger.info(
            f"EnhancedSelector initialized: llm_enabled={self.llm_enabled}, "
            f"rerank_method={self.rerank_method}"
        )

    def fetch_news_for_stocks(
        self,
        symbols: List[str],
        lookback_days: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Fetch and format news for multiple stocks.

        Args:
            symbols: List of stock symbols
            lookback_days: Days to look back for news

        Returns:
            Dictionary mapping symbol to formatted news summary
        """
        if lookback_days is None:
            lookback_days = self.news_lookback_days

        logger.info(f"Fetching news for {len(symbols)} stocks...")

        news_summaries = {}

        for symbol in symbols:
            try:
                # Get news articles (get_news expects a list)
                news_dict = self.data_manager.get_news(
                    [symbol],
                    lookback_days=lookback_days
                )

                # Extract articles for this symbol
                news_articles = news_dict.get(symbol, [])

                # Format for LLM prompt
                news_summary = PromptTemplate.format_news_for_prompt(
                    news_articles,
                    max_articles=20,  # Increased from 5 to use enhanced capacity
                    max_chars=3000,   # Increased from 1500 to use enhanced capacity
                    prioritize_important=True  # Enable prioritization
                )

                news_summaries[symbol] = news_summary

            except Exception as e:
                logger.warning(f"Failed to fetch news for {symbol}: {e}")
                news_summaries[symbol] = "No recent news available."

        logger.success(f"Fetched news for {len(news_summaries)}/{len(symbols)} stocks")

        return news_summaries

    def score_with_llm(
        self,
        selected_stocks: pd.DataFrame,
        news_summaries: Dict[str, str],
        universe_info: Optional[pd.DataFrame] = None,
        store_prompts: bool = False,
        prompt_store = None,
        fetch_earnings: bool = True
    ) -> pd.DataFrame:
        """
        Score stocks using LLM.

        Args:
            selected_stocks: DataFrame with momentum-selected stocks
            news_summaries: Dictionary of news summaries per symbol
            universe_info: Optional universe info with company names/sectors
            store_prompts: Whether to store prompts for viewing
            prompt_store: PromptStore instance (if None, creates new one)
            fetch_earnings: Whether to fetch earnings data (default: True)

        Returns:
            DataFrame with LLM scores added
        """
        if not self.llm_enabled:
            logger.warning("LLM scoring disabled, skipping")
            return selected_stocks

        logger.info(f"Scoring {len(selected_stocks)} stocks with LLM...")

        # Initialize prompt store if needed
        if store_prompts and prompt_store is None:
            from ..llm import get_prompt_store
            prompt_store = get_prompt_store()

        # Fetch earnings data if enabled
        earnings_data_dict = {}
        if fetch_earnings:
            try:
                symbols = selected_stocks['symbol'].tolist()
                logger.info(f"Fetching earnings data for {len(symbols)} stocks...")
                earnings_data_dict = self.data_manager.get_earnings(
                    symbols,
                    use_cache=True,
                    show_progress=False
                )
                logger.success(f"Fetched earnings for {len(earnings_data_dict)}/{len(symbols)} stocks")
            except Exception as e:
                logger.warning(f"Failed to fetch earnings data: {e}")
                earnings_data_dict = {}

        # Fetch analyst data (Phase 3)
        analyst_data_dict = {}
        try:
            symbols = selected_stocks['symbol'].tolist()
            logger.info(f"Fetching analyst data for {len(symbols)} stocks...")
            analyst_data_dict = self.data_manager.get_analyst_data(
                symbols,
                use_cache=True,
                show_progress=False
            )
            logger.success(f"Fetched analyst data for {len(analyst_data_dict)}/{len(symbols)} stocks")
        except Exception as e:
            logger.warning(f"Failed to fetch analyst data: {e}")
            analyst_data_dict = {}

        # Prepare batch data
        stocks_data = []

        for _, row in selected_stocks.iterrows():
            symbol = row['symbol']

            # Get company info if available
            company_info = None
            if universe_info is not None and symbol in universe_info.index:
                company_row = universe_info.loc[symbol]
                company_info = {
                    'name': company_row.get('name', symbol),
                    'sector': company_row.get('sector', 'Unknown')
                }

            stocks_data.append({
                'symbol': symbol,
                'news_summary': news_summaries.get(symbol, ''),
                'momentum_return': row.get('momentum_return'),
                'company_info': company_info,
                'earnings_data': earnings_data_dict.get(symbol),
                'analyst_data': analyst_data_dict.get(symbol)
            })

        # Score stocks and optionally store prompts
        all_scores = {}
        all_prompts = {}

        for stock_data in stocks_data:
            symbol = stock_data['symbol']

            # Score with prompt return if storing
            result = self.llm_scorer.score_stock(
                symbol=symbol,
                news_summary=stock_data['news_summary'],
                momentum_return=stock_data['momentum_return'],
                company_info=stock_data['company_info'],
                earnings_data=stock_data.get('earnings_data'),
                analyst_data=stock_data.get('analyst_data'),
                return_prompt=store_prompts
            )

            if result is not None:
                if store_prompts:
                    raw_score, normalized_score, prompt = result
                    all_prompts[symbol] = prompt

                    # Store prompt
                    if prompt_store:
                        prompt_store.store_prompt(
                            symbol=symbol,
                            prompt=prompt,
                            prompt_type='llm_scoring',
                            metadata={
                                'model': self.llm_scorer.model,
                                'raw_score': raw_score,
                                'normalized_score': normalized_score
                            }
                        )
                else:
                    raw_score, normalized_score = result

                all_scores[symbol] = (raw_score, normalized_score)

        # Add scores to DataFrame
        result = selected_stocks.copy()

        result['llm_raw_score'] = result['symbol'].map(
            lambda s: all_scores[s][0] if s in all_scores else None
        )
        result['llm_score'] = result['symbol'].map(
            lambda s: all_scores[s][1] if s in all_scores else None
        )

        # Store prompts in DataFrame if available
        if store_prompts:
            result['llm_prompt'] = result['symbol'].map(
                lambda s: all_prompts.get(s, None)
            )

        # Track scoring success
        scored_count = result['llm_score'].notna().sum()
        logger.success(f"Successfully scored {scored_count}/{len(result)} stocks with LLM")

        if store_prompts:
            logger.info(f"Stored prompts for {len(all_prompts)} stocks")

        return result

    def rerank_by_llm(
        self,
        stocks_with_scores: pd.DataFrame,
        method: str = 'llm_only'
    ) -> pd.DataFrame:
        """
        Re-rank stocks based on LLM scores.

        Args:
            stocks_with_scores: DataFrame with momentum_return and llm_score
            method: Re-ranking method
                - 'llm_only': Rank purely by LLM score
                - 'combined': Average of momentum rank and LLM rank
                - 'weighted': Weighted combination (configurable)

        Returns:
            Re-ranked DataFrame
        """
        result = stocks_with_scores.copy()

        # Filter out stocks without LLM scores
        has_llm = result['llm_score'].notna()
        result_scored = result[has_llm].copy()

        if len(result_scored) == 0:
            logger.warning("No stocks have LLM scores, returning original ranking")
            return result

        if method == 'llm_only':
            # Rank purely by LLM score (descending)
            result_scored = result_scored.sort_values('llm_score', ascending=False)
            result_scored['final_rank'] = range(1, len(result_scored) + 1)

            logger.info(f"Re-ranked {len(result_scored)} stocks by LLM score only")

        elif method == 'combined':
            # Average of momentum rank and LLM rank
            result_scored['momentum_rank_norm'] = result_scored['rank'] / len(result)
            result_scored['llm_rank'] = result_scored['llm_score'].rank(ascending=False)
            result_scored['llm_rank_norm'] = result_scored['llm_rank'] / len(result_scored)

            # Average the normalized ranks
            result_scored['combined_rank_norm'] = (
                result_scored['momentum_rank_norm'] + result_scored['llm_rank_norm']
            ) / 2

            result_scored = result_scored.sort_values('combined_rank_norm')
            result_scored['final_rank'] = range(1, len(result_scored) + 1)

            logger.info(f"Re-ranked {len(result_scored)} stocks by combined momentum + LLM")

        elif method == 'weighted':
            # Weighted combination (70% momentum, 30% LLM by default)
            momentum_weight = 0.7
            llm_weight = 0.3

            result_scored['momentum_rank_norm'] = result_scored['rank'] / len(result)
            result_scored['llm_rank'] = result_scored['llm_score'].rank(ascending=False)
            result_scored['llm_rank_norm'] = result_scored['llm_rank'] / len(result_scored)

            result_scored['weighted_rank_norm'] = (
                momentum_weight * result_scored['momentum_rank_norm'] +
                llm_weight * result_scored['llm_rank_norm']
            )

            result_scored = result_scored.sort_values('weighted_rank_norm')
            result_scored['final_rank'] = range(1, len(result_scored) + 1)

            logger.info(
                f"Re-ranked {len(result_scored)} stocks by weighted "
                f"(momentum={momentum_weight}, llm={llm_weight})"
            )

        else:
            logger.warning(f"Unknown rerank method '{method}', using llm_only")
            return self.rerank_by_llm(stocks_with_scores, method='llm_only')

        # Add back stocks without LLM scores at the end
        if has_llm.sum() < len(result):
            no_llm = result[~has_llm].copy()
            no_llm['final_rank'] = range(
                len(result_scored) + 1,
                len(result_scored) + len(no_llm) + 1
            )
            result_scored = pd.concat([result_scored, no_llm], ignore_index=True)

        return result_scored

    def select_for_portfolio_enhanced(
        self,
        price_data: Dict[str, pd.DataFrame],
        end_date: Optional[str] = None,
        apply_quality_filter: bool = True,
        final_count: Optional[int] = None,
        rerank_method: Optional[str] = None,
        store_prompts: bool = False,
        prompt_store = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Enhanced selection pipeline with LLM re-ranking.

        Args:
            price_data: Dictionary mapping symbols to price DataFrames
            end_date: End date for calculations
            apply_quality_filter: Whether to apply data quality filters
            final_count: Final number of stocks to select (default: config)
            rerank_method: Re-ranking method to use

        Returns:
            Tuple of (selected_stocks_df, metadata_dict)
        """
        if final_count is None:
            final_count = self.final_portfolio_size

        if rerank_method is None:
            rerank_method = self.rerank_method

        metadata = {
            'selection_date': end_date or datetime.now().strftime('%Y-%m-%d'),
            'initial_universe': len(price_data),
            'after_quality_filter': 0,
            'after_momentum_calc': 0,
            'after_momentum_selection': 0,
            'after_llm_scoring': 0,
            'final_selected': 0,
            'llm_enabled': self.llm_enabled,
            'rerank_method': rerank_method
        }

        # Step 1-3: Baseline momentum selection (top 20%)
        logger.info("="*70)
        logger.info("ENHANCED SELECTION PIPELINE")
        logger.info("="*70)

        baseline_selected, baseline_metadata = self.select_for_portfolio(
            price_data,
            end_date=end_date,
            apply_quality_filter=apply_quality_filter
        )

        # Update metadata
        metadata.update(baseline_metadata)
        metadata['after_momentum_selection'] = len(baseline_selected)

        if baseline_selected.empty:
            logger.warning("No stocks from baseline momentum selection")
            return pd.DataFrame(), metadata

        logger.info(
            f"\nBaseline momentum selection: {len(baseline_selected)} stocks "
            f"(top {self.top_percentile*100:.0f}%)"
        )

        # Step 4: Fetch news if LLM enabled
        if not self.llm_enabled:
            logger.info("LLM disabled, returning baseline selection")
            metadata['final_selected'] = len(baseline_selected)
            return baseline_selected.head(final_count), metadata

        logger.info("\nStep 4: Fetching news for LLM scoring...")
        symbols = baseline_selected['symbol'].tolist()
        news_summaries = self.fetch_news_for_stocks(symbols)

        # Step 5: Get company info for better prompts
        try:
            universe_info = self.data_manager.get_universe_info()
        except:
            universe_info = None

        # Step 6: Score with LLM
        logger.info("\nStep 5: Scoring stocks with LLM...")
        stocks_with_scores = self.score_with_llm(
            baseline_selected,
            news_summaries,
            universe_info,
            store_prompts=store_prompts,
            prompt_store=prompt_store
        )

        metadata['after_llm_scoring'] = stocks_with_scores['llm_score'].notna().sum()

        # Step 7: Re-rank by LLM scores
        logger.info(f"\nStep 6: Re-ranking by LLM scores ({rerank_method})...")
        reranked = self.rerank_by_llm(stocks_with_scores, method=rerank_method)

        # Step 8: Select final portfolio
        final_selected = reranked.head(final_count)
        metadata['final_selected'] = len(final_selected)

        logger.success(
            f"\n{'='*70}\n"
            f"Enhanced selection complete:\n"
            f"  Initial universe: {metadata['initial_universe']}\n"
            f"  After momentum selection: {metadata['after_momentum_selection']}\n"
            f"  After LLM scoring: {metadata['after_llm_scoring']}\n"
            f"  Final selected: {metadata['final_selected']}\n"
            f"{'='*70}"
        )

        return final_selected, metadata

    def get_enhanced_summary(
        self,
        selected_df: pd.DataFrame,
        metadata: Dict
    ) -> str:
        """
        Generate summary for enhanced selection.

        Args:
            selected_df: Selected stocks DataFrame
            metadata: Selection metadata

        Returns:
            Formatted summary string
        """
        if selected_df.empty:
            return "No stocks selected"

        summary_parts = [
            "=" * 70,
            "ENHANCED STOCK SELECTION SUMMARY (with LLM)",
            "=" * 70,
            f"Selection Date: {metadata['selection_date']}",
            f"LLM Enabled: {metadata['llm_enabled']}",
            f"Re-rank Method: {metadata['rerank_method']}",
            "",
            "Pipeline Results:",
            f"  Initial Universe:         {metadata['initial_universe']:>6} stocks",
            f"  After Quality Filter:     {metadata['after_quality_filter']:>6} stocks",
            f"  After Momentum Calc:      {metadata['after_momentum_calc']:>6} stocks",
            f"  After Momentum Selection: {metadata['after_momentum_selection']:>6} stocks (top 20%)",
            f"  After LLM Scoring:        {metadata['after_llm_scoring']:>6} stocks scored",
            f"  Final Selected:           {metadata['final_selected']:>6} stocks",
            "",
        ]

        # Momentum and LLM statistics
        if 'llm_score' in selected_df.columns:
            has_scores = selected_df['llm_score'].notna()

            summary_parts.extend([
                "Momentum Statistics:",
                f"  Mean Return:   {selected_df['momentum_return'].mean():>7.2%}",
                f"  Median Return: {selected_df['momentum_return'].median():>7.2%}",
                "",
                "LLM Score Statistics:",
                f"  Stocks Scored: {has_scores.sum():>6}/{len(selected_df)}",
            ])

            if has_scores.any():
                summary_parts.extend([
                    f"  Mean Score:    {selected_df.loc[has_scores, 'llm_score'].mean():>7.3f}",
                    f"  Median Score:  {selected_df.loc[has_scores, 'llm_score'].median():>7.3f}",
                    f"  Min Score:     {selected_df.loc[has_scores, 'llm_score'].min():>7.3f}",
                    f"  Max Score:     {selected_df.loc[has_scores, 'llm_score'].max():>7.3f}",
                ])

        # Top 10 stocks
        summary_parts.extend([
            "",
            "Top 10 Selected Stocks:",
            f"{'Rank':<6} {'Symbol':<8} {'Momentum':>10} {'LLM Score':>10} {'Final Rank':>10}"
        ])
        summary_parts.append("-" * 70)

        top_10 = selected_df.head(10)
        for _, row in top_10.iterrows():
            momentum_str = f"{row['momentum_return']:>9.2%}" if pd.notna(row['momentum_return']) else "N/A"
            llm_str = f"{row['llm_score']:>9.3f}" if pd.notna(row.get('llm_score')) else "N/A"
            final_rank = row.get('final_rank', row.get('rank', '?'))

            summary_parts.append(
                f"{row['rank']:<6} {row['symbol']:<8} {momentum_str} {llm_str} {final_rank:>10}"
            )

        summary_parts.append("=" * 70)

        return "\n".join(summary_parts)


def main():
    """Test enhanced selector."""
    from src.data import DataManager

    logger.info("Testing Enhanced Stock Selector with LLM")
    logger.info("="*70)

    # Initialize
    dm = DataManager()
    selector = EnhancedSelector()

    # Get sample universe
    logger.info("Fetching sample universe...")
    universe = dm.get_universe()[:100]  # First 100 stocks

    logger.info(f"Fetching price data for {len(universe)} stocks...")
    price_data = dm.get_prices(universe, use_cache=True, show_progress=True)

    # Run enhanced selection
    logger.info("\nRunning enhanced selection pipeline...")
    selected, metadata = selector.select_for_portfolio_enhanced(
        price_data,
        apply_quality_filter=True,
        final_count=20,  # Select top 20 stocks
        rerank_method='llm_only'
    )

    # Display results
    if not selected.empty:
        summary = selector.get_enhanced_summary(selected, metadata)
        print("\n" + summary)

        # Compare with baseline
        logger.info("\n" + "="*70)
        logger.info("COMPARISON: Enhanced vs Baseline")
        logger.info("="*70)

        if 'llm_score' in selected.columns and selected['llm_score'].notna().any():
            top_5_enhanced = selected.head(5)['symbol'].tolist()
            top_5_baseline = selected.nsmallest(5, 'rank')['symbol'].tolist()

            logger.info(f"\nTop 5 by LLM ranking: {', '.join(top_5_enhanced)}")
            logger.info(f"Top 5 by momentum:    {', '.join(top_5_baseline)}")

            # Check if different
            if top_5_enhanced != top_5_baseline:
                logger.info("\n✓ LLM re-ranking changed the selection!")
            else:
                logger.info("\n→ LLM ranking matches momentum ranking")

    else:
        logger.warning("No stocks selected")


if __name__ == "__main__":
    main()

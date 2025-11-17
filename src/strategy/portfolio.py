"""
Portfolio Construction Module
Constructs and manages portfolios from selected stocks.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Dict, Optional, Tuple
import yaml


class PortfolioConstructor:
    """
    Constructs portfolios from selected stocks using various weighting schemes.

    Supports:
    - Equal weighting
    - Value weighting (market-cap based)
    - Momentum-score weighting
    - Position size constraints
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize portfolio constructor.

        Args:
            config_path: Path to strategy configuration
        """
        self.config = self._load_config(config_path)

        # Extract portfolio parameters
        strategy_config = self.config.get('strategy', {})
        self.initial_weighting = strategy_config.get('initial_weighting', 'equal')
        self.max_position_weight = strategy_config.get('max_position_weight', 0.15)
        self.final_portfolio_size = strategy_config.get('final_portfolio_size', 50)

        logger.info(
            f"PortfolioConstructor initialized: weighting={self.initial_weighting}, "
            f"max_position={self.max_position_weight}, target_size={self.final_portfolio_size}"
        )

    def _load_config(self, path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def equal_weight(
        self,
        selected_stocks: pd.DataFrame,
        max_position: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Create equal-weighted portfolio.

        Args:
            selected_stocks: DataFrame with selected stocks
            max_position: Maximum weight per position (default: self.max_position_weight)

        Returns:
            DataFrame with weights added
        """
        if selected_stocks.empty:
            return selected_stocks

        if max_position is None:
            max_position = self.max_position_weight

        portfolio = selected_stocks.copy()
        n_stocks = len(portfolio)

        # Equal weight
        equal_wt = 1.0 / n_stocks

        # Check if equal weight exceeds max
        if equal_wt > max_position:
            logger.warning(
                f"Equal weight ({equal_wt:.2%}) exceeds max position ({max_position:.2%}). "
                f"Limiting to max and redistributing."
            )
            # Cap at max and redistribute remainder
            portfolio['weight'] = max_position
        else:
            portfolio['weight'] = equal_wt

        # Normalize to ensure sum = 1
        portfolio['weight'] = portfolio['weight'] / portfolio['weight'].sum()

        logger.info(
            f"Equal-weighted portfolio: {len(portfolio)} stocks, "
            f"avg weight: {portfolio['weight'].mean():.2%}"
        )

        return portfolio

    def value_weight(
        self,
        selected_stocks: pd.DataFrame,
        price_data: Dict[str, pd.DataFrame],
        max_position: Optional[float] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Create value-weighted (market-cap) portfolio.

        Args:
            selected_stocks: DataFrame with selected stocks
            price_data: Dictionary of price DataFrames
            max_position: Maximum weight per position
            end_date: Date for valuation (default: latest)

        Returns:
            DataFrame with weights added
        """
        if selected_stocks.empty:
            return selected_stocks

        if max_position is None:
            max_position = self.max_position_weight

        portfolio = selected_stocks.copy()

        # Get market cap approximation (price * volume)
        market_caps = {}

        for symbol in portfolio['symbol']:
            if symbol not in price_data or price_data[symbol] is None:
                logger.warning(f"{symbol}: No price data for market cap calculation")
                continue

            df = price_data[symbol]

            # Filter by end_date if specified
            if end_date:
                df = df[df.index <= end_date]

            if df.empty:
                continue

            # Use last available price and volume
            if 'adjusted_close' in df.columns and 'volume' in df.columns:
                price = df['adjusted_close'].iloc[-1]
                volume = df['volume'].tail(21).mean()  # Average volume
                market_caps[symbol] = price * volume
            else:
                logger.warning(f"{symbol}: Missing price or volume data")

        if not market_caps:
            logger.warning("No market cap data available, falling back to equal weight")
            return self.equal_weight(selected_stocks, max_position)

        # Calculate weights proportional to market cap
        total_market_cap = sum(market_caps.values())

        weights = {}
        for symbol, market_cap in market_caps.items():
            weights[symbol] = market_cap / total_market_cap

        # Add weights to portfolio
        portfolio['raw_weight'] = portfolio['symbol'].map(weights)

        # Apply position size constraint
        portfolio['weight'] = portfolio['raw_weight'].clip(upper=max_position)

        # Normalize
        portfolio['weight'] = portfolio['weight'] / portfolio['weight'].sum()

        # Count constrained positions
        n_constrained = (portfolio['raw_weight'] > max_position).sum()
        if n_constrained > 0:
            logger.info(f"{n_constrained} positions constrained to {max_position:.2%}")

        logger.info(
            f"Value-weighted portfolio: {len(portfolio)} stocks, "
            f"avg weight: {portfolio['weight'].mean():.2%}, "
            f"max weight: {portfolio['weight'].max():.2%}"
        )

        return portfolio

    def momentum_weight(
        self,
        selected_stocks: pd.DataFrame,
        max_position: Optional[float] = None,
        scaling_factor: float = 1.0
    ) -> pd.DataFrame:
        """
        Create momentum-weighted portfolio (higher momentum = higher weight).

        Args:
            selected_stocks: DataFrame with momentum_return column
            max_position: Maximum weight per position
            scaling_factor: Controls concentration (higher = more concentrated)

        Returns:
            DataFrame with weights added
        """
        if selected_stocks.empty:
            return selected_stocks

        if max_position is None:
            max_position = self.max_position_weight

        if 'momentum_return' not in selected_stocks.columns:
            logger.warning("No momentum_return column, falling back to equal weight")
            return self.equal_weight(selected_stocks, max_position)

        portfolio = selected_stocks.copy()

        # Shift momentum to positive (add abs(min) + small constant)
        min_momentum = portfolio['momentum_return'].min()
        if min_momentum < 0:
            shifted_momentum = portfolio['momentum_return'] + abs(min_momentum) + 0.01
        else:
            shifted_momentum = portfolio['momentum_return'] + 0.01

        # Apply scaling
        scaled_momentum = shifted_momentum ** scaling_factor

        # Calculate weights
        portfolio['raw_weight'] = scaled_momentum / scaled_momentum.sum()

        # Apply position constraint
        portfolio['weight'] = portfolio['raw_weight'].clip(upper=max_position)

        # Normalize
        portfolio['weight'] = portfolio['weight'] / portfolio['weight'].sum()

        logger.info(
            f"Momentum-weighted portfolio: {len(portfolio)} stocks, "
            f"avg weight: {portfolio['weight'].mean():.2%}, "
            f"max weight: {portfolio['weight'].max():.2%}"
        )

        return portfolio

    def construct_portfolio(
        self,
        selected_stocks: pd.DataFrame,
        price_data: Optional[Dict[str, pd.DataFrame]] = None,
        weighting_scheme: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Construct portfolio using specified weighting scheme.

        Args:
            selected_stocks: DataFrame with selected stocks
            price_data: Dictionary of price DataFrames (required for value weighting)
            weighting_scheme: 'equal', 'value', or 'momentum' (default: from config)
            end_date: Date for portfolio construction

        Returns:
            DataFrame with portfolio holdings and weights
        """
        if selected_stocks.empty:
            logger.warning("No stocks provided for portfolio construction")
            return pd.DataFrame()

        if weighting_scheme is None:
            weighting_scheme = self.initial_weighting

        logger.info(
            f"Constructing {weighting_scheme}-weighted portfolio with "
            f"{len(selected_stocks)} stocks"
        )

        # Apply weighting scheme
        if weighting_scheme == 'equal':
            portfolio = self.equal_weight(selected_stocks)

        elif weighting_scheme == 'value':
            if price_data is None:
                logger.warning("Price data required for value weighting, using equal weight")
                portfolio = self.equal_weight(selected_stocks)
            else:
                portfolio = self.value_weight(selected_stocks, price_data, end_date=end_date)

        elif weighting_scheme == 'momentum':
            portfolio = self.momentum_weight(selected_stocks)

        else:
            logger.warning(f"Unknown weighting scheme '{weighting_scheme}', using equal weight")
            portfolio = self.equal_weight(selected_stocks)

        # Add construction metadata
        portfolio['construction_date'] = end_date or datetime.now().strftime('%Y-%m-%d')
        portfolio['weighting_scheme'] = weighting_scheme

        # Verify weights sum to 1
        weight_sum = portfolio['weight'].sum()
        if not np.isclose(weight_sum, 1.0, atol=1e-6):
            logger.warning(f"Portfolio weights sum to {weight_sum:.6f}, normalizing")
            portfolio['weight'] = portfolio['weight'] / weight_sum

        return portfolio

    def get_portfolio_summary(self, portfolio: pd.DataFrame) -> Dict:
        """
        Get summary statistics for portfolio.

        Args:
            portfolio: Portfolio DataFrame with weights

        Returns:
            Dictionary with summary statistics
        """
        if portfolio.empty or 'weight' not in portfolio.columns:
            return {'num_holdings': 0}

        summary = {
            'num_holdings': len(portfolio),
            'avg_weight': portfolio['weight'].mean(),
            'max_weight': portfolio['weight'].max(),
            'min_weight': portfolio['weight'].min(),
            'weight_std': portfolio['weight'].std(),
            'concentration': (portfolio['weight'] ** 2).sum(),  # Herfindahl index
        }

        # Add momentum stats if available
        if 'momentum_return' in portfolio.columns:
            summary['avg_momentum'] = portfolio['momentum_return'].mean()
            summary['weighted_avg_momentum'] = (
                portfolio['momentum_return'] * portfolio['weight']
            ).sum()

        # Top 5 holdings
        top_5 = portfolio.nlargest(5, 'weight')[['symbol', 'weight']]
        summary['top_5_holdings'] = top_5.to_dict('records')

        return summary

    def format_portfolio_report(self, portfolio: pd.DataFrame) -> str:
        """
        Generate human-readable portfolio report.

        Args:
            portfolio: Portfolio DataFrame

        Returns:
            Formatted report string
        """
        if portfolio.empty:
            return "Empty portfolio"

        summary = self.get_portfolio_summary(portfolio)

        report_parts = [
            "=" * 70,
            "Portfolio Holdings Report",
            "=" * 70,
            f"Date: {portfolio['construction_date'].iloc[0] if 'construction_date' in portfolio.columns else 'N/A'}",
            f"Weighting Scheme: {portfolio['weighting_scheme'].iloc[0] if 'weighting_scheme' in portfolio.columns else 'N/A'}",
            "",
            "Summary Statistics:",
            f"  Number of Holdings:     {summary['num_holdings']:>6}",
            f"  Average Weight:         {summary['avg_weight']:>6.2%}",
            f"  Max Weight:             {summary['max_weight']:>6.2%}",
            f"  Min Weight:             {summary['min_weight']:>6.2%}",
            f"  Concentration (HHI):    {summary['concentration']:>6.4f}",
            "",
        ]

        if 'avg_momentum' in summary:
            report_parts.extend([
                "Momentum Statistics:",
                f"  Average Momentum:       {summary['avg_momentum']:>6.2%}",
                f"  Weighted Avg Momentum:  {summary['weighted_avg_momentum']:>6.2%}",
                "",
            ])

        report_parts.append("Top 10 Holdings:")
        report_parts.append(f"{'Rank':<6} {'Symbol':<8} {'Weight':>8} {'Momentum':>10}")
        report_parts.append("-" * 70)

        # Show top 10
        top_holdings = portfolio.nlargest(10, 'weight')
        for idx, row in enumerate(top_holdings.itertuples(), 1):
            momentum_str = f"{row.momentum_return:>9.2%}" if 'momentum_return' in portfolio.columns else "N/A"
            report_parts.append(
                f"{idx:<6} {row.symbol:<8} {row.weight:>7.2%} {momentum_str}"
            )

        report_parts.append("=" * 70)

        return "\n".join(report_parts)

    def export_portfolio(
        self,
        portfolio: pd.DataFrame,
        output_path: str,
        include_all_columns: bool = False
    ):
        """
        Export portfolio to CSV.

        Args:
            portfolio: Portfolio DataFrame
            output_path: Path to save CSV
            include_all_columns: Include all metadata columns
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if include_all_columns:
            portfolio.to_csv(output_file, index=False)
        else:
            # Export essential columns
            essential_cols = ['symbol', 'weight']
            if 'momentum_return' in portfolio.columns:
                essential_cols.append('momentum_return')
            if 'rank' in portfolio.columns:
                essential_cols.append('rank')

            portfolio[essential_cols].to_csv(output_file, index=False)

        logger.info(f"Exported portfolio to {output_file}")


def main():
    """Test portfolio constructor."""
    from src.data import DataManager
    from src.strategy import StockSelector

    # Initialize
    dm = DataManager()
    selector = StockSelector()
    constructor = PortfolioConstructor()

    # Get sample stocks
    logger.info("Fetching data for sample stocks...")
    universe = dm.get_universe()[:50]
    price_data = dm.get_prices(universe, use_cache=True, show_progress=False)

    # Select stocks
    logger.info("\nSelecting stocks...")
    selected_stocks, metadata = selector.select_for_portfolio(price_data)

    if selected_stocks.empty:
        logger.error("No stocks selected")
        return

    # Test different weighting schemes
    schemes = ['equal', 'value', 'momentum']

    for scheme in schemes:
        logger.info(f"\n{'='*70}")
        logger.info(f"Testing {scheme.upper()} weighting")
        logger.info(f"{'='*70}")

        portfolio = constructor.construct_portfolio(
            selected_stocks,
            price_data=price_data,
            weighting_scheme=scheme
        )

        # Display report
        report = constructor.format_portfolio_report(portfolio)
        print("\n" + report)

        # Get summary
        summary = constructor.get_portfolio_summary(portfolio)
        logger.info(f"\nTop 5 Holdings:")
        for holding in summary['top_5_holdings']:
            logger.info(f"  {holding['symbol']}: {holding['weight']:.2%}")


if __name__ == "__main__":
    main()

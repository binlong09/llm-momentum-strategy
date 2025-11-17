"""
Enhanced Portfolio Constructor with LLM Weight Tilting
Extends baseline portfolio construction with LLM-based weight tilting.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, Optional
import yaml

from .portfolio import PortfolioConstructor
from .volatility_protection import VolatilityProtection


class EnhancedPortfolioConstructor(PortfolioConstructor):
    """
    Enhanced portfolio constructor with LLM-based weight tilting.

    Implements the weight tilting mechanism from the paper:
    - Base weights from momentum/value/equal weighting
    - Tilt toward stocks with higher LLM scores
    - Controlled by η (eta) parameter
    """

    def __init__(self, config_path: str = "config/config.yaml", enable_volatility_protection: bool = False):
        """
        Initialize enhanced portfolio constructor.

        Args:
            config_path: Path to strategy configuration
            enable_volatility_protection: Whether to enable volatility protection
        """
        super().__init__(config_path)

        # Extract weight tilting parameters
        strategy_config = self.config.get('strategy', {})
        self.weight_tilt_factor = strategy_config.get('weight_tilt_factor', 5.0)

        # Initialize volatility protection if enabled
        self.enable_volatility_protection = enable_volatility_protection
        self.vol_protect = None
        if enable_volatility_protection:
            self.vol_protect = VolatilityProtection()
            logger.info("Volatility protection enabled")

        logger.info(
            f"EnhancedPortfolioConstructor initialized: "
            f"base_weighting={self.initial_weighting}, "
            f"tilt_factor={self.weight_tilt_factor}, "
            f"volatility_protection={enable_volatility_protection}"
        )

    def llm_tilted_weight(
        self,
        selected_stocks: pd.DataFrame,
        base_weighting: str = 'equal',
        tilt_factor: Optional[float] = None,
        max_position: Optional[float] = None,
        price_data: Optional[Dict[str, pd.DataFrame]] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Create LLM-tilted portfolio weights.

        Process:
        1. Calculate base weights (equal, value, or momentum)
        2. Tilt weights toward higher LLM scores using η factor
        3. Apply position size constraints
        4. Normalize to sum to 1

        Args:
            selected_stocks: DataFrame with LLM scores
            base_weighting: Base weighting scheme ('equal', 'value', 'momentum')
            tilt_factor: η parameter (higher = more tilting)
            max_position: Maximum weight per position
            price_data: Required for value weighting
            end_date: Required for value weighting

        Returns:
            DataFrame with tilted weights
        """
        if tilt_factor is None:
            tilt_factor = self.weight_tilt_factor

        if max_position is None:
            max_position = self.max_position_weight

        if selected_stocks.empty:
            return selected_stocks

        # Check if LLM scores are available
        if 'llm_score' not in selected_stocks.columns:
            logger.warning("No LLM scores found, falling back to base weighting")
            return self.construct_portfolio(
                selected_stocks,
                price_data=price_data,
                weighting_scheme=base_weighting,
                end_date=end_date
            )

        portfolio = selected_stocks.copy()

        # Step 1: Calculate base weights
        logger.info(f"Calculating base weights using {base_weighting} scheme...")

        if base_weighting == 'equal':
            base_portfolio = self.equal_weight(portfolio, max_position=1.0)  # No constraint yet
        elif base_weighting == 'value':
            if price_data is None:
                logger.warning("Price data required for value weighting, using equal weight")
                base_portfolio = self.equal_weight(portfolio, max_position=1.0)
            else:
                base_portfolio = self.value_weight(
                    portfolio, price_data, max_position=1.0, end_date=end_date
                )
        elif base_weighting == 'momentum':
            base_portfolio = self.momentum_weight(portfolio, max_position=1.0)
        else:
            logger.warning(f"Unknown base weighting '{base_weighting}', using equal")
            base_portfolio = self.equal_weight(portfolio, max_position=1.0)

        # Step 2: Apply LLM tilting
        logger.info(f"Applying LLM weight tilting (η={tilt_factor})...")

        # Filter stocks with LLM scores
        has_llm = base_portfolio['llm_score'].notna()
        tilted_portfolio = base_portfolio[has_llm].copy()

        if len(tilted_portfolio) == 0:
            logger.warning("No stocks with LLM scores, returning base weights")
            return base_portfolio

        # Shift LLM scores to positive range if needed
        # LLM scores are in [-1, 1], shift to [0, 2]
        shifted_scores = tilted_portfolio['llm_score'] + 1.0

        # Apply power tilting: weight ∝ base_weight * (score ^ η)
        # Higher η means more concentration in high-scoring stocks
        tilt_multiplier = shifted_scores ** tilt_factor

        # Apply tilting
        tilted_portfolio['tilted_weight'] = (
            tilted_portfolio['weight'] * tilt_multiplier
        )

        # Normalize
        tilted_portfolio['tilted_weight'] = (
            tilted_portfolio['tilted_weight'] / tilted_portfolio['tilted_weight'].sum()
        )

        # Step 3: Apply position constraints
        tilted_portfolio['weight'] = tilted_portfolio['tilted_weight'].clip(upper=max_position)

        # Renormalize after constraint
        tilted_portfolio['weight'] = (
            tilted_portfolio['weight'] / tilted_portfolio['weight'].sum()
        )

        # Count constrained positions
        n_constrained = (tilted_portfolio['tilted_weight'] > max_position).sum()
        if n_constrained > 0:
            logger.info(f"{n_constrained} positions constrained to {max_position:.2%}")

        # Add back stocks without LLM scores at minimal weight
        if has_llm.sum() < len(base_portfolio):
            no_llm = base_portfolio[~has_llm].copy()
            # Give minimal weight to stocks without LLM scores
            no_llm['weight'] = 0.001
            tilted_portfolio = pd.concat([tilted_portfolio, no_llm], ignore_index=True)

            # Final normalization
            tilted_portfolio['weight'] = (
                tilted_portfolio['weight'] / tilted_portfolio['weight'].sum()
            )

        logger.info(
            f"LLM-tilted portfolio: {len(tilted_portfolio)} stocks, "
            f"avg weight: {tilted_portfolio['weight'].mean():.2%}, "
            f"max weight: {tilted_portfolio['weight'].max():.2%}"
        )

        return tilted_portfolio

    def calculate_risk_weighted_adjustment(
        self,
        portfolio: pd.DataFrame,
        market_exposure: float
    ) -> pd.DataFrame:
        """
        Apply risk-weighted protection (Option 3): high-risk stocks get extra reduction.

        Args:
            portfolio: Portfolio with risk_score column
            market_exposure: Overall market exposure from volatility protection (0.0-1.0)

        Returns:
            Portfolio with risk-weighted adjustments
        """
        adjusted = portfolio.copy()

        # Calculate risk-based multiplier for each stock
        def calculate_risk_multiplier(risk_score, market_exposure):
            """
            Calculate combined multiplier based on both market and stock risk.

            Low risk (0.0-0.4): Market exposure only
            Medium risk (0.4-0.7): Market exposure + 10% extra cut
            High risk (0.7-1.0): Market exposure + 30% extra cut
            """
            if risk_score < 0.4:
                return market_exposure
            elif risk_score < 0.7:
                extra_reduction = 0.90
                return market_exposure * extra_reduction
            else:
                extra_reduction = 0.70
                return market_exposure * extra_reduction

        # Store original weights
        adjusted['original_weight_before_combined'] = adjusted['weight']

        # Apply risk-weighted adjustment
        adjusted['combined_multiplier'] = adjusted['risk_score'].apply(
            lambda r: calculate_risk_multiplier(r, market_exposure)
        )

        adjusted['weight'] = adjusted['weight'] * adjusted['combined_multiplier']

        # Renormalize
        adjusted['weight'] = adjusted['weight'] / adjusted['weight'].sum()

        return adjusted

    def apply_volatility_protection(
        self,
        portfolio: pd.DataFrame,
        spy_prices: pd.Series,
        spy_returns: pd.Series,
        vix_level: float,
        momentum_returns: pd.Series,
        current_date: datetime,
        enable_hedging: bool = False,
        use_risk_weighting: bool = True
    ) -> tuple[pd.DataFrame, Dict]:
        """
        Apply volatility protection adjustments to portfolio weights.

        If portfolio has risk_score column and use_risk_weighting=True,
        applies risk-weighted protection (Option 3).

        Args:
            portfolio: Portfolio DataFrame with weights
            spy_prices: SPY price series
            spy_returns: SPY returns series
            vix_level: Current VIX level
            momentum_returns: Strategy returns series
            current_date: Current date
            enable_hedging: Whether to enable short hedging
            use_risk_weighting: Whether to apply risk-weighted protection (Option 3)

        Returns:
            Tuple of (adjusted_portfolio, adjustments_dict)
        """
        if self.vol_protect is None:
            logger.warning("Volatility protection not initialized")
            return portfolio, {}

        # Get protection adjustments
        adjustments = self.vol_protect.calculate_combined_adjustment(
            spy_prices=spy_prices,
            spy_returns=spy_returns,
            vix_level=vix_level,
            momentum_returns=momentum_returns,
            current_date=current_date,
            enable_hedging=enable_hedging
        )

        # Apply exposure adjustment
        adjusted_portfolio = portfolio.copy()
        adjusted_portfolio['original_weight'] = adjusted_portfolio['weight']

        # Check if we should apply risk-weighted protection
        has_risk_scores = 'risk_score' in adjusted_portfolio.columns

        if use_risk_weighting and has_risk_scores:
            logger.info("Applying risk-weighted protection (Option 3)...")
            adjusted_portfolio = self.calculate_risk_weighted_adjustment(
                adjusted_portfolio,
                market_exposure=adjustments['final_exposure']
            )
            protection_type = "Risk-Weighted"
        else:
            # Standard uniform protection
            adjusted_portfolio['weight'] = adjusted_portfolio['weight'] * adjustments['final_exposure']
            protection_type = "Uniform"

        # Calculate cash position
        cash_position = 1.0 - adjusted_portfolio['weight'].sum()

        logger.info(
            f"Volatility protection applied ({protection_type}): "
            f"regime={adjustments['regime'].state}, "
            f"base_exposure={adjustments['final_exposure']:.1%}, "
            f"cash={cash_position:.1%}"
        )

        # Add protection metadata
        adjusted_portfolio['protection_regime'] = adjustments['regime'].state
        adjusted_portfolio['protection_exposure'] = adjustments['final_exposure']
        adjusted_portfolio['protection_type'] = protection_type

        return adjusted_portfolio, adjustments

    def construct_portfolio_enhanced(
        self,
        selected_stocks: pd.DataFrame,
        price_data: Optional[Dict[str, pd.DataFrame]] = None,
        base_weighting: Optional[str] = None,
        use_llm_tilting: bool = True,
        tilt_factor: Optional[float] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Construct enhanced portfolio with optional LLM tilting.

        Args:
            selected_stocks: DataFrame with selected stocks (must have llm_score if tilting)
            price_data: Dictionary of price DataFrames
            base_weighting: Base weighting scheme
            use_llm_tilting: Whether to apply LLM tilting
            tilt_factor: Tilting parameter η
            end_date: Date for portfolio construction

        Returns:
            DataFrame with portfolio holdings and weights
        """
        if selected_stocks.empty:
            logger.warning("No stocks provided for portfolio construction")
            return pd.DataFrame()

        if base_weighting is None:
            base_weighting = self.initial_weighting

        # Check if LLM tilting is requested and possible
        if use_llm_tilting and 'llm_score' in selected_stocks.columns:
            logger.info(
                f"Constructing LLM-tilted portfolio: "
                f"base={base_weighting}, η={tilt_factor or self.weight_tilt_factor}"
            )

            portfolio = self.llm_tilted_weight(
                selected_stocks,
                base_weighting=base_weighting,
                tilt_factor=tilt_factor,
                price_data=price_data,
                end_date=end_date
            )

        else:
            # Fall back to baseline portfolio construction
            if use_llm_tilting:
                logger.warning("LLM tilting requested but no LLM scores available")

            logger.info(f"Constructing baseline {base_weighting}-weighted portfolio")

            portfolio = self.construct_portfolio(
                selected_stocks,
                price_data=price_data,
                weighting_scheme=base_weighting,
                end_date=end_date
            )

        # Add metadata
        portfolio['construction_date'] = end_date or datetime.now().strftime('%Y-%m-%d')
        portfolio['weighting_scheme'] = f"{base_weighting}_{'llm_tilted' if use_llm_tilting else 'baseline'}"

        # Verify weights sum to 1
        weight_sum = portfolio['weight'].sum()
        if not np.isclose(weight_sum, 1.0, atol=1e-6):
            logger.warning(f"Portfolio weights sum to {weight_sum:.6f}, normalizing")
            portfolio['weight'] = portfolio['weight'] / weight_sum

        return portfolio

    def compare_tilting_factors(
        self,
        selected_stocks: pd.DataFrame,
        tilt_factors: list = None,
        base_weighting: str = 'equal',
        price_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[float, pd.DataFrame]:
        """
        Compare portfolios with different tilting factors.

        Args:
            selected_stocks: Stocks with LLM scores
            tilt_factors: List of η values to test
            base_weighting: Base weighting scheme
            price_data: Price data for value weighting

        Returns:
            Dictionary mapping η to portfolio DataFrame
        """
        if tilt_factors is None:
            tilt_factors = [0.0, 1.0, 3.0, 5.0, 10.0]

        if 'llm_score' not in selected_stocks.columns:
            logger.error("Cannot compare tilting without LLM scores")
            return {}

        logger.info(f"Comparing {len(tilt_factors)} tilting factors: {tilt_factors}")

        portfolios = {}

        for eta in tilt_factors:
            logger.info(f"\nTesting η={eta}...")

            portfolio = self.llm_tilted_weight(
                selected_stocks,
                base_weighting=base_weighting,
                tilt_factor=eta,
                price_data=price_data
            )

            portfolios[eta] = portfolio

            # Show top 3 holdings
            top_3 = portfolio.nlargest(3, 'weight')[['symbol', 'weight', 'llm_score']]
            logger.info(f"  Top 3 holdings:")
            for _, row in top_3.iterrows():
                logger.info(f"    {row['symbol']}: {row['weight']:.2%} (LLM: {row['llm_score']:.3f})")

        return portfolios


def main():
    """Test enhanced portfolio constructor."""
    from src.data import DataManager
    from src.strategy import EnhancedSelector

    logger.info("Testing Enhanced Portfolio Constructor")
    logger.info("="*70)

    # Initialize
    dm = DataManager()
    selector = EnhancedSelector()
    constructor = EnhancedPortfolioConstructor()

    # Get sample data
    logger.info("Fetching sample data...")
    universe = dm.get_universe()[:50]
    price_data = dm.get_prices(universe, use_cache=True, show_progress=False)

    # Select stocks with LLM
    logger.info("\nRunning enhanced selection...")
    selected, metadata = selector.select_for_portfolio_enhanced(
        price_data,
        final_count=10
    )

    if selected.empty:
        logger.error("No stocks selected")
        return

    # Test different tilting factors
    logger.info("\n" + "="*70)
    logger.info("TESTING WEIGHT TILTING")
    logger.info("="*70)

    portfolios = constructor.compare_tilting_factors(
        selected,
        tilt_factors=[0.0, 2.0, 5.0, 10.0],
        base_weighting='equal',
        price_data=price_data
    )

    # Summary comparison
    logger.info("\n" + "="*70)
    logger.info("TILTING FACTOR COMPARISON")
    logger.info("="*70)

    print(f"\n{'η Factor':<12} {'Max Weight':>12} {'HHI':>12} {'Avg Score':>12}")
    print("-" * 70)

    for eta, portfolio in sorted(portfolios.items()):
        max_weight = portfolio['weight'].max()
        hhi = (portfolio['weight'] ** 2).sum()  # Herfindahl index
        avg_score = portfolio['llm_score'].mean()

        print(f"{eta:<12.1f} {max_weight:>11.2%} {hhi:>12.4f} {avg_score:>12.3f}")

    logger.info("\n" + "="*70)
    logger.info("Note:")
    logger.info("  - Higher η = more weight concentration")
    logger.info("  - HHI (Herfindahl Index): higher = more concentrated")
    logger.info("  - η=0 is pure equal weight")
    logger.info("  - η=5 is paper's optimal parameter")
    logger.info("="*70)


if __name__ == "__main__":
    main()

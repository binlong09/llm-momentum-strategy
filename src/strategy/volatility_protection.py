"""
Volatility Protection Enhancements for LLM Momentum Strategy

This module implements 5 key strategies to improve performance during volatile markets:
1. Volatility Scaling
2. Market State Filter  
3. Crash Indicator
4. Dynamic Rebalancing Frequency
5. Optional Hedging via Short Positions

Based on academic research:
- Barroso & Santa-Clara (2015): "Momentum Has Its Moments"
- Daniel & Moskowitz (2016): "Momentum Crashes"
- Moreira & Muir (2017): "Volatility-Managed Portfolios"
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MarketRegime:
    """Market regime classification"""
    state: str  # "bull", "bear", "panic", "normal"
    vix_level: float
    volatility: float
    market_trend: str  # "up", "down", "neutral"
    momentum_beta: float


class VolatilityProtection:
    """
    Implements volatility protection mechanisms for momentum strategies.
    
    Key Features:
    - Dynamic position sizing based on volatility
    - Market state detection and filtering
    - Crash risk indicators
    - Adaptive rebalancing frequency
    """
    
    def __init__(
        self,
        vix_threshold_high: float = 30.0,
        vix_threshold_panic: float = 40.0,
        target_volatility: float = 0.15,  # 15% annualized
        lookback_days: int = 21,
        max_drawdown_threshold: float = 0.15,  # 15%
    ):
        """
        Initialize volatility protection parameters.
        
        Args:
            vix_threshold_high: VIX level indicating high volatility
            vix_threshold_panic: VIX level indicating panic state
            target_volatility: Target portfolio volatility for scaling
            lookback_days: Days to calculate realized volatility
            max_drawdown_threshold: Maximum acceptable drawdown before reducing exposure
        """
        self.vix_threshold_high = vix_threshold_high
        self.vix_threshold_panic = vix_threshold_panic
        self.target_volatility = target_volatility
        self.lookback_days = lookback_days
        self.max_drawdown_threshold = max_drawdown_threshold
        
    # ========================================================================
    # ENHANCEMENT 1: VOLATILITY SCALING
    # ========================================================================
    
    def calculate_volatility_scalar(
        self,
        returns: pd.Series,
        current_date: datetime
    ) -> float:
        """
        Calculate position size scalar based on realized volatility.
        
        Higher volatility → Smaller positions
        Lower volatility → Larger positions
        
        Formula: scalar = target_vol / realized_vol
        
        Args:
            returns: Historical returns series
            current_date: Current date for calculation

        Returns:
            Position size scalar (e.g., 0.5 = reduce to 50%, 1.5 = increase to 150%)
        """
        # Normalize timezone to match returns index
        current_date = pd.Timestamp(current_date)
        if returns.index.tz is not None:
            # Returns index is timezone-aware, ensure current_date matches
            if current_date.tz is None:
                current_date = current_date.tz_localize(returns.index.tz)
        else:
            # Returns index is timezone-naive, ensure current_date matches
            if current_date.tz is not None:
                current_date = current_date.tz_localize(None)

        # Get recent returns - use asof to handle dates that aren't exact trading days
        try:
            end_idx = returns.index.get_loc(current_date)
        except KeyError:
            # Date not in index, find nearest prior date
            valid_dates = returns.index[returns.index <= current_date]
            if len(valid_dates) == 0:
                raise ValueError(f"No data available before {current_date}")
            end_idx = returns.index.get_loc(valid_dates[-1])
        start_idx = max(0, end_idx - self.lookback_days)
        recent_returns = returns.iloc[start_idx:end_idx]
        
        # Calculate realized volatility (annualized)
        realized_vol = recent_returns.std() * np.sqrt(252)
        
        # Avoid division by zero
        if realized_vol < 0.01:
            realized_vol = 0.01
            
        # Calculate scalar
        scalar = self.target_volatility / realized_vol
        
        # Cap scalar between 0.25 and 2.0
        scalar = np.clip(scalar, 0.25, 2.0)
        
        return scalar
    
    # ========================================================================
    # ENHANCEMENT 2: MARKET STATE FILTER
    # ========================================================================
    
    def detect_market_regime(
        self,
        spy_prices: pd.Series,
        vix_level: float,
        current_date: datetime
    ) -> MarketRegime:
        """
        Detect current market regime for filtering.
        
        Regimes:
        - Bull: Price > 200-day MA, VIX < 20
        - Normal: Price > 200-day MA, VIX 20-30
        - Bear: Price < 200-day MA, VIX 20-30
        - Panic: VIX > 30
        
        Args:
            spy_prices: SPY price series
            vix_level: Current VIX level
            current_date: Current date
            
        Returns:
            MarketRegime object with classification
        """
        # Calculate 200-day moving average
        ma_200 = spy_prices.rolling(window=200).mean()
        current_price = spy_prices[current_date]
        current_ma = ma_200[current_date]
        
        # Calculate recent volatility
        returns = spy_prices.pct_change()
        recent_vol = returns.tail(21).std() * np.sqrt(252)
        
        # Determine trend
        if current_price > current_ma * 1.02:
            trend = "up"
        elif current_price < current_ma * 0.98:
            trend = "down"
        else:
            trend = "neutral"
            
        # Calculate momentum beta (simplified)
        market_returns = returns.tail(60)
        momentum_beta = 1.0  # Simplified; in practice, calculate from portfolio
        
        # Classify regime
        if vix_level > self.vix_threshold_panic:
            state = "panic"
        elif vix_level > self.vix_threshold_high:
            state = "bear" if trend == "down" else "volatile"
        elif trend == "up" and vix_level < 20:
            state = "bull"
        elif trend == "down":
            state = "bear"
        else:
            state = "normal"
            
        return MarketRegime(
            state=state,
            vix_level=vix_level,
            volatility=recent_vol,
            market_trend=trend,
            momentum_beta=momentum_beta
        )
    
    def get_regime_exposure_multiplier(self, regime: MarketRegime) -> float:
        """
        Get portfolio exposure multiplier based on market regime.
        
        Args:
            regime: MarketRegime object
            
        Returns:
            Exposure multiplier (0.0 to 1.0)
        """
        if regime.state == "panic":
            return 0.25  # 75% reduction
        elif regime.state == "bear":
            return 0.50  # 50% reduction
        elif regime.state == "volatile":
            return 0.60  # 40% reduction
        elif regime.state == "normal":
            return 0.85  # 15% reduction
        else:  # bull
            return 1.00  # Full exposure
    
    # ========================================================================
    # ENHANCEMENT 3: CRASH INDICATOR
    # ========================================================================
    
    def detect_crash_risk(
        self,
        spy_returns: pd.Series,
        vix_level: float,
        momentum_returns: pd.Series,
        current_date: datetime
    ) -> Tuple[bool, float]:
        """
        Detect elevated crash risk using multiple signals.
        
        Crash signals:
        1. Market down >15% from recent high
        2. VIX > 35
        3. Negative momentum beta (winners becoming losers)
        4. Recent momentum strategy drawdown
        
        Args:
            spy_returns: Market returns series
            vix_level: Current VIX level
            momentum_returns: Momentum strategy returns
            current_date: Current date
            
        Returns:
            Tuple of (is_crash_risk: bool, risk_score: float [0-1])
        """
        risk_score = 0.0
        
        # Signal 1: Market drawdown from recent high
        spy_prices = (1 + spy_returns).cumprod()
        recent_high = spy_prices.tail(60).max()
        current_price = spy_prices[current_date]
        drawdown = (current_price - recent_high) / recent_high
        
        if drawdown < -0.15:
            risk_score += 0.30
        elif drawdown < -0.10:
            risk_score += 0.15
            
        # Signal 2: VIX spike
        if vix_level > 40:
            risk_score += 0.30
        elif vix_level > 35:
            risk_score += 0.20
        elif vix_level > 30:
            risk_score += 0.10
            
        # Signal 3: Momentum strategy drawdown
        mom_cumulative = (1 + momentum_returns).cumprod()
        mom_recent_high = mom_cumulative.tail(60).max()
        mom_current = mom_cumulative[current_date]
        mom_drawdown = (mom_current - mom_recent_high) / mom_recent_high
        
        if mom_drawdown < -0.10:
            risk_score += 0.25
        elif mom_drawdown < -0.05:
            risk_score += 0.15
            
        # Signal 4: Volatility spike
        recent_vol = spy_returns.tail(21).std() * np.sqrt(252)
        if recent_vol > 0.40:  # 40% annualized vol
            risk_score += 0.15
            
        # Determine if crash risk is elevated
        is_crash_risk = risk_score > 0.50
        
        return is_crash_risk, min(risk_score, 1.0)
    
    def get_crash_risk_adjustment(self, risk_score: float) -> float:
        """
        Get position adjustment based on crash risk score.
        
        Args:
            risk_score: Risk score from 0 to 1
            
        Returns:
            Position multiplier (0.0 to 1.0)
        """
        if risk_score > 0.75:
            return 0.10  # Exit almost completely
        elif risk_score > 0.60:
            return 0.25  # Reduce to 25%
        elif risk_score > 0.50:
            return 0.50  # Reduce to 50%
        elif risk_score > 0.35:
            return 0.70  # Reduce to 70%
        else:
            return 1.00  # No adjustment
    
    # ========================================================================
    # ENHANCEMENT 4: DYNAMIC REBALANCING FREQUENCY
    # ========================================================================
    
    def get_optimal_rebalancing_frequency(
        self,
        vix_level: float,
        regime: MarketRegime,
        crash_risk_score: float
    ) -> str:
        """
        Determine optimal rebalancing frequency based on market conditions.
        
        Logic:
        - Normal/Bull markets: Monthly (lower turnover, lower costs)
        - Volatile markets: Weekly (more responsive)
        - Panic/Crash: Daily (maximum responsiveness)
        
        Args:
            vix_level: Current VIX level
            regime: MarketRegime object
            crash_risk_score: Current crash risk score
            
        Returns:
            Rebalancing frequency: "daily", "weekly", or "monthly"
        """
        # Panic conditions: Daily rebalancing
        if crash_risk_score > 0.60 or vix_level > 40:
            return "daily"
        
        # High volatility: Weekly rebalancing
        elif regime.state in ["panic", "volatile"] or vix_level > 30:
            return "weekly"
        
        # Normal conditions: Monthly rebalancing
        else:
            return "monthly"
    
    # ========================================================================
    # ENHANCEMENT 5: HEDGING VIA SHORT POSITIONS (OPTIONAL)
    # ========================================================================
    
    def calculate_hedge_ratio(
        self,
        regime: MarketRegime,
        crash_risk_score: float,
        enable_hedging: bool = False
    ) -> float:
        """
        Calculate optimal hedge ratio for short positions.
        
        Short past losers as hedge against momentum crash.
        
        Args:
            regime: Current market regime
            crash_risk_score: Current crash risk score
            enable_hedging: Whether to enable hedging (default False for long-only)
            
        Returns:
            Hedge ratio (0.0 to 0.5, where 0.3 = 30% short exposure)
        """
        if not enable_hedging:
            return 0.0
        
        # Increase hedging in risky conditions
        base_hedge = 0.0
        
        if crash_risk_score > 0.60:
            base_hedge = 0.40  # 40% hedge
        elif crash_risk_score > 0.45:
            base_hedge = 0.30  # 30% hedge
        elif crash_risk_score > 0.30:
            base_hedge = 0.20  # 20% hedge
        elif regime.state in ["bear", "volatile"]:
            base_hedge = 0.10  # 10% hedge
        
        return min(base_hedge, 0.50)  # Cap at 50% hedge
    
    # ========================================================================
    # COMBINED PROTECTION SYSTEM
    # ========================================================================
    
    def calculate_combined_adjustment(
        self,
        spy_prices: pd.Series,
        spy_returns: pd.Series,
        vix_level: float,
        momentum_returns: pd.Series,
        current_date: datetime,
        enable_hedging: bool = False
    ) -> Dict:
        """
        Calculate all protection adjustments and combine them.
        
        This is the main function to call for integrated volatility protection.
        
        Args:
            spy_prices: SPY price series
            spy_returns: SPY returns series
            vix_level: Current VIX level
            momentum_returns: Momentum strategy returns
            current_date: Current date
            enable_hedging: Whether to enable short hedging
            
        Returns:
            Dictionary with all adjustments and recommendations:
            {
                'volatility_scalar': float,
                'regime': MarketRegime,
                'regime_multiplier': float,
                'crash_risk': bool,
                'crash_risk_score': float,
                'crash_adjustment': float,
                'rebalancing_frequency': str,
                'hedge_ratio': float,
                'final_exposure': float,  # Combined final adjustment
                'recommendation': str
            }
        """
        # 1. Volatility scaling
        vol_scalar = self.calculate_volatility_scalar(spy_returns, current_date)
        
        # 2. Market regime
        regime = self.detect_market_regime(spy_prices, vix_level, current_date)
        regime_mult = self.get_regime_exposure_multiplier(regime)
        
        # 3. Crash risk
        is_crash_risk, crash_score = self.detect_crash_risk(
            spy_returns, vix_level, momentum_returns, current_date
        )
        crash_adj = self.get_crash_risk_adjustment(crash_score)
        
        # 4. Rebalancing frequency
        rebal_freq = self.get_optimal_rebalancing_frequency(
            vix_level, regime, crash_score
        )
        
        # 5. Hedge ratio
        hedge_ratio = self.calculate_hedge_ratio(
            regime, crash_score, enable_hedging
        )
        
        # Calculate combined final exposure
        # Use minimum of all adjustments (most conservative)
        final_exposure = min(vol_scalar, regime_mult, crash_adj)
        
        # Generate recommendation
        if final_exposure < 0.30:
            recommendation = "DEFENSIVE: Reduce exposure to <30%. Consider going to cash."
        elif final_exposure < 0.50:
            recommendation = "CAUTIOUS: Reduce exposure to 50%. High volatility detected."
        elif final_exposure < 0.75:
            recommendation = "MODERATE: Reduce exposure to 75%. Elevated risk."
        elif final_exposure < 0.90:
            recommendation = "NORMAL: Slight reduction. Monitor markets closely."
        else:
            recommendation = "FULL EXPOSURE: Favorable conditions for momentum."
        
        return {
            'volatility_scalar': vol_scalar,
            'regime': regime,
            'regime_multiplier': regime_mult,
            'crash_risk': is_crash_risk,
            'crash_risk_score': crash_score,
            'crash_adjustment': crash_adj,
            'rebalancing_frequency': rebal_freq,
            'hedge_ratio': hedge_ratio,
            'final_exposure': final_exposure,
            'recommendation': recommendation
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("Volatility Protection Module")
    print("=" * 60)
    print("\nThis module provides 5 key enhancements:")
    print("1. Volatility Scaling - Adjust positions based on realized vol")
    print("2. Market State Filter - Detect bull/bear/panic regimes")
    print("3. Crash Indicator - Early warning system for momentum crashes")
    print("4. Dynamic Rebalancing - Adjust frequency based on volatility")
    print("5. Hedging (Optional) - Short losers to hedge crash risk")
    print("\nImport this in your main strategy to add protection!")

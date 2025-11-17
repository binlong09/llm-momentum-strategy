# Volatility Protection Integration Guide

This guide shows how to integrate the 5 volatility protection enhancements into your LLM momentum strategy.

## Quick Start

### 1. Basic Integration

```python
from src.strategy.volatility_protection import VolatilityProtection

# Initialize protection system
vol_protect = VolatilityProtection(
    vix_threshold_high=30.0,
    vix_threshold_panic=40.0,
    target_volatility=0.15,
    lookback_days=21
)

# Get current adjustments
adjustments = vol_protect.calculate_combined_adjustment(
    spy_prices=spy_price_series,
    spy_returns=spy_return_series,
    vix_level=current_vix,
    momentum_returns=your_momentum_returns,
    current_date=today,
    enable_hedging=False  # Set True for short hedging
)

# Apply to your portfolio
final_weights = base_weights * adjustments['final_exposure']
```

### 2. Integration with Main Strategy

Modify your portfolio construction to include protection:

```python
def build_enhanced_portfolio(
    momentum_candidates,
    llm_scores,
    market_data,
    vol_protection
):
    """Build LLM-enhanced portfolio with volatility protection"""
    
    # Step 1: Base LLM-enhanced portfolio (your existing code)
    portfolio = construct_llm_portfolio(momentum_candidates, llm_scores)
    
    # Step 2: Get volatility protection adjustments
    adjustments = vol_protection.calculate_combined_adjustment(
        spy_prices=market_data['spy_prices'],
        spy_returns=market_data['spy_returns'],
        vix_level=market_data['vix'],
        momentum_returns=portfolio.returns,
        current_date=market_data['date']
    )
    
    # Step 3: Apply adjustments to weights
    for stock in portfolio:
        stock.weight *= adjustments['final_exposure']
    
    # Step 4: Adjust rebalancing frequency if needed
    portfolio.rebalancing_frequency = adjustments['rebalancing_frequency']
    
    # Step 5: Log recommendation
    print(f"Protection Status: {adjustments['recommendation']}")
    print(f"Final Exposure: {adjustments['final_exposure']:.1%}")
    print(f"Regime: {adjustments['regime'].state}")
    print(f"Crash Risk: {adjustments['crash_risk_score']:.2f}")
    
    return portfolio, adjustments
```

## Detailed Integration Examples

### Example 1: Monthly Rebalancing with Protection

```python
import pandas as pd
from datetime import datetime
from src.strategy.volatility_protection import VolatilityProtection

class ProtectedMomentumStrategy:
    def __init__(self):
        self.vol_protect = VolatilityProtection()
        
    def rebalance_portfolio(self, date):
        # 1. Get momentum candidates (your existing code)
        candidates = self.get_momentum_candidates(date)
        
        # 2. Get LLM scores (your existing code)
        llm_scores = self.score_with_llm(candidates)
        
        # 3. Select top stocks
        selected = self.select_top_stocks(candidates, llm_scores, n=50)
        
        # 4. Calculate base weights
        base_weights = self.calculate_base_weights(selected)
        
        # 5. Get protection adjustments
        adjustments = self.vol_protect.calculate_combined_adjustment(
            spy_prices=self.market_data['spy_prices'],
            spy_returns=self.market_data['spy_returns'],
            vix_level=self.get_vix(date),
            momentum_returns=self.strategy_returns,
            current_date=date
        )
        
        # 6. Apply protection
        final_weights = {}
        for ticker, weight in base_weights.items():
            final_weights[ticker] = weight * adjustments['final_exposure']
        
        # 7. Normalize weights
        total = sum(final_weights.values())
        final_weights = {k: v/total for k, v in final_weights.items()}
        
        return final_weights, adjustments
```

### Example 2: Real-Time Monitoring Dashboard

```python
def print_protection_dashboard(adjustments):
    """Print a dashboard of current protection status"""
    
    print("\n" + "="*60)
    print("VOLATILITY PROTECTION DASHBOARD")
    print("="*60)
    
    # Market Regime
    regime = adjustments['regime']
    print(f"\n📊 MARKET REGIME: {regime.state.upper()}")
    print(f"   VIX Level: {regime.vix_level:.1f}")
    print(f"   Volatility: {regime.volatility:.1%}")
    print(f"   Trend: {regime.market_trend}")
    
    # Protection Levels
    print(f"\n🛡️ PROTECTION ADJUSTMENTS:")
    print(f"   Volatility Scalar: {adjustments['volatility_scalar']:.2f}x")
    print(f"   Regime Multiplier: {adjustments['regime_multiplier']:.1%}")
    print(f"   Crash Adjustment: {adjustments['crash_adjustment']:.1%}")
    
    # Risk Assessment
    print(f"\n⚠️  RISK ASSESSMENT:")
    print(f"   Crash Risk: {'YES ⚠️' if adjustments['crash_risk'] else 'NO ✓'}")
    print(f"   Risk Score: {adjustments['crash_risk_score']:.2f}/1.00")
    
    # Actions
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   Portfolio Exposure: {adjustments['final_exposure']:.1%}")
    print(f"   Rebalancing: {adjustments['rebalancing_frequency'].upper()}")
    print(f"   Hedge Ratio: {adjustments['hedge_ratio']:.1%}")
    
    print(f"\n💡 {adjustments['recommendation']}")
    print("="*60 + "\n")
```

### Example 3: Backtesting with Protection

```python
def backtest_with_protection(start_date, end_date):
    """Backtest strategy with volatility protection enabled"""
    
    results = {
        'dates': [],
        'returns': [],
        'exposures': [],
        'regimes': [],
        'crash_risks': []
    }
    
    vol_protect = VolatilityProtection()
    current_portfolio = None
    
    for date in pd.date_range(start_date, end_date, freq='B'):  # Business days
        
        # Get market data
        spy_prices = get_spy_prices(date)
        spy_returns = spy_prices.pct_change()
        vix = get_vix(date)
        
        # Check if we need to rebalance
        if should_rebalance(date, current_portfolio):
            
            # Get protection adjustments
            adjustments = vol_protect.calculate_combined_adjustment(
                spy_prices=spy_prices,
                spy_returns=spy_returns,
                vix_level=vix,
                momentum_returns=calculate_momentum_returns(date),
                current_date=date
            )
            
            # Build protected portfolio
            current_portfolio = build_protected_portfolio(
                date=date,
                exposure_multiplier=adjustments['final_exposure']
            )
            
            # Store metrics
            results['exposures'].append(adjustments['final_exposure'])
            results['regimes'].append(adjustments['regime'].state)
            results['crash_risks'].append(adjustments['crash_risk_score'])
        
        # Calculate daily return
        daily_return = calculate_portfolio_return(current_portfolio, date)
        results['dates'].append(date)
        results['returns'].append(daily_return)
    
    # Calculate performance metrics
    returns_series = pd.Series(results['returns'], index=results['dates'])
    sharpe = calculate_sharpe(returns_series)
    max_dd = calculate_max_drawdown(returns_series)
    
    print(f"Backtest Results with Protection:")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f"  Max Drawdown: {max_dd:.1%}")
    print(f"  Avg Exposure: {np.mean(results['exposures']):.1%}")
    
    return results
```

## Configuration Recommendations

### Conservative Setup (Risk-Averse)
```python
vol_protect = VolatilityProtection(
    vix_threshold_high=25.0,      # Earlier response
    vix_threshold_panic=35.0,     # Lower panic threshold
    target_volatility=0.10,       # Lower target vol (10%)
    max_drawdown_threshold=0.10   # Exit at 10% drawdown
)
```

### Balanced Setup (Default)
```python
vol_protect = VolatilityProtection(
    vix_threshold_high=30.0,
    vix_threshold_panic=40.0,
    target_volatility=0.15,
    max_drawdown_threshold=0.15
)
```

### Aggressive Setup (Higher Risk Tolerance)
```python
vol_protect = VolatilityProtection(
    vix_threshold_high=35.0,      # Later response
    vix_threshold_panic=45.0,     # Higher panic threshold
    target_volatility=0.20,       # Higher target vol (20%)
    max_drawdown_threshold=0.20   # Tolerate 20% drawdown
)
```

## Testing the Protection System

```python
# Test script
if __name__ == "__main__":
    from src.strategy.volatility_protection import VolatilityProtection
    import yfinance as yf
    
    # Download test data
    spy = yf.download('SPY', start='2020-01-01', end='2020-12-31')
    vix = yf.download('^VIX', start='2020-01-01', end='2020-12-31')
    
    # Initialize protection
    vol_protect = VolatilityProtection()
    
    # Test on COVID crash (March 2020)
    test_date = pd.Timestamp('2020-03-16')
    
    spy_returns = spy['Close'].pct_change()
    momentum_returns = spy_returns  # Simplified
    
    adjustments = vol_protect.calculate_combined_adjustment(
        spy_prices=spy['Close'],
        spy_returns=spy_returns,
        vix_level=vix['Close'][test_date],
        momentum_returns=momentum_returns,
        current_date=test_date
    )
    
    print(f"\nMarch 16, 2020 (COVID Crash Peak):")
    print(f"  VIX: {vix['Close'][test_date]:.1f}")
    print(f"  Regime: {adjustments['regime'].state}")
    print(f"  Crash Risk: {adjustments['crash_risk']}")
    print(f"  Recommended Exposure: {adjustments['final_exposure']:.1%}")
    print(f"  Rebalancing: {adjustments['rebalancing_frequency']}")
```

## Key Benefits

✅ **Reduced Drawdowns**: Automatically reduce exposure in high-risk periods  
✅ **Better Risk-Adjusted Returns**: Higher Sharpe ratio through volatility management  
✅ **Crash Protection**: Early warning system for momentum crashes  
✅ **Adaptive**: Changes behavior based on market conditions  
✅ **Easy to Use**: Drop-in integration with existing strategy  

## Performance Impact (Expected)

Based on academic research, adding these protections should:

| Metric | Without Protection | With Protection |
|--------|-------------------|-----------------|
| Sharpe Ratio | 0.7 - 1.0 | 1.0 - 1.5 |
| Max Drawdown | -25% to -35% | -10% to -20% |
| Volatility | 20-25% | 15-20% |
| Turnover | Medium | Medium-High |

## Next Steps

1. Copy `volatility_protection.py` to your project
2. Integrate into your portfolio construction
3. Backtest with protection enabled
4. Compare protected vs unprotected performance
5. Tune thresholds based on your risk tolerance

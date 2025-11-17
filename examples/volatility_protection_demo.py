#!/usr/bin/env python3
"""
Example: Using Volatility Protection in LLM Momentum Strategy

This script demonstrates how to integrate the 5 volatility protection
enhancements into your momentum trading strategy.
"""

import sys
sys.path.append('..')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategy.volatility_protection import VolatilityProtection


def example_1_basic_usage():
    """Example 1: Basic usage of volatility protection"""
    
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Volatility Protection Usage")
    print("="*70)
    
    # Initialize protection system
    vol_protect = VolatilityProtection(
        vix_threshold_high=30.0,
        vix_threshold_panic=40.0,
        target_volatility=0.15
    )
    
    # Simulate market data
    dates = pd.date_range('2020-01-01', '2020-12-31', freq='B')
    np.random.seed(42)
    spy_prices = pd.Series(
        100 * np.exp(np.random.randn(len(dates)).cumsum() * 0.01),
        index=dates
    )
    spy_returns = spy_prices.pct_change().fillna(0)
    
    # Test different VIX scenarios
    scenarios = [
        ("Low Volatility (VIX=15)", 15.0),
        ("Normal Market (VIX=20)", 20.0),
        ("High Volatility (VIX=35)", 35.0),
        ("Panic Mode (VIX=50)", 50.0),
    ]
    
    for scenario_name, vix_level in scenarios:
        adjustments = vol_protect.calculate_combined_adjustment(
            spy_prices=spy_prices,
            spy_returns=spy_returns,
            vix_level=vix_level,
            momentum_returns=spy_returns,  # Simplified
            current_date=dates[-1]
        )
        
        print(f"\n{scenario_name}:")
        print(f"  Regime: {adjustments['regime'].state}")
        print(f"  Final Exposure: {adjustments['final_exposure']:.1%}")
        print(f"  Rebalancing: {adjustments['rebalancing_frequency']}")
        print(f"  Crash Risk: {adjustments['crash_risk_score']:.2f}")


def example_2_march_2020_covid_crash():
    """Example 2: How protection would have worked during COVID crash"""
    
    print("\n" + "="*70)
    print("EXAMPLE 2: COVID-19 Crash (March 2020)")
    print("="*70)
    
    try:
        import yfinance as yf
        
        # Download real data
        print("\nDownloading market data...")
        spy = yf.download('SPY', start='2020-02-01', end='2020-04-30', progress=False)
        vix_data = yf.download('^VIX', start='2020-02-01', end='2020-04-30', progress=False)
        
        vol_protect = VolatilityProtection()
        
        # Key dates during COVID crash
        key_dates = [
            ('2020-02-20', 'Pre-Crash Peak'),
            ('2020-03-09', 'First Major Drop'),
            ('2020-03-16', 'Peak Panic'),
            ('2020-03-23', 'Market Bottom'),
            ('2020-04-15', 'Recovery Phase'),
        ]
        
        print("\nProtection System Recommendations During COVID Crash:")
        print("-" * 70)
        
        spy_prices = spy['Close']
        spy_returns = spy_prices.pct_change()

        for date_str, description in key_dates:
            date = pd.Timestamp(date_str)

            # Find nearest available date
            if date not in spy.index:
                nearest_dates = spy.index[spy.index >= date]
                if len(nearest_dates) == 0:
                    continue
                date = nearest_dates[0]

            if date not in vix_data.index:
                nearest_vix_dates = vix_data.index[vix_data.index >= date]
                if len(nearest_vix_dates) == 0:
                    continue
                vix_date = nearest_vix_dates[0]
            else:
                vix_date = date

            vix_level = vix_data['Close'][vix_date]
            
            adjustments = vol_protect.calculate_combined_adjustment(
                spy_prices=spy_prices,
                spy_returns=spy_returns,
                vix_level=vix_level,
                momentum_returns=spy_returns,
                current_date=date
            )
            
            print(f"\n{date_str} - {description}:")
            print(f"  SPY Price: ${spy_prices[date]:.2f}")
            print(f"  VIX: {vix_level:.1f}")
            print(f"  Regime: {adjustments['regime'].state}")
            print(f"  Crash Risk Score: {adjustments['crash_risk_score']:.2f}")
            print(f"  📊 EXPOSURE: {adjustments['final_exposure']:.1%}")
            print(f"  🔄 REBALANCING: {adjustments['rebalancing_frequency']}")
            print(f"  💡 {adjustments['recommendation']}")
        
    except ImportError:
        print("\n⚠️  yfinance not installed. Install with: pip install yfinance")
        print("Skipping real market data example...")


def example_3_portfolio_integration():
    """Example 3: Integrating with portfolio construction"""
    
    print("\n" + "="*70)
    print("EXAMPLE 3: Portfolio Integration")
    print("="*70)
    
    # Simulate a momentum portfolio
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
    base_weights = {ticker: 1.0/len(tickers) for ticker in tickers}
    
    print("\nBase Portfolio (Equal-Weighted):")
    for ticker, weight in base_weights.items():
        print(f"  {ticker}: {weight:.2%}")
    
    # Simulate market conditions
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='B')
    spy_prices = pd.Series(100 * (1 + np.random.randn(len(dates)).cumsum() * 0.01), index=dates)
    spy_returns = spy_prices.pct_change().fillna(0)
    
    vol_protect = VolatilityProtection()
    
    # Test under different market conditions
    test_conditions = [
        ("Normal Market", 18.0),
        ("Volatile Market", 32.0),
        ("Crisis Mode", 45.0),
    ]
    
    for condition_name, vix_level in test_conditions:
        print(f"\n{'='*70}")
        print(f"{condition_name} (VIX={vix_level})")
        print(f"{'='*70}")
        
        adjustments = vol_protect.calculate_combined_adjustment(
            spy_prices=spy_prices,
            spy_returns=spy_returns,
            vix_level=vix_level,
            momentum_returns=spy_returns,
            current_date=dates[-1]
        )
        
        # Apply adjustment to portfolio
        adjusted_weights = {
            ticker: weight * adjustments['final_exposure']
            for ticker, weight in base_weights.items()
        }
        
        # Calculate cash position
        cash_position = 1.0 - sum(adjusted_weights.values())
        
        print(f"\nAdjusted Portfolio:")
        for ticker, weight in adjusted_weights.items():
            print(f"  {ticker}: {weight:.2%}")
        print(f"  CASH: {cash_position:.2%}")
        print(f"\nTotal Equity Exposure: {sum(adjusted_weights.values()):.1%}")
        print(f"Protection Level: {(1-adjustments['final_exposure']):.1%}")


def example_4_backtesting_comparison():
    """Example 4: Compare performance with vs without protection"""
    
    print("\n" + "="*70)
    print("EXAMPLE 4: Backtest Comparison")
    print("="*70)
    
    # Simulate strategy returns
    np.random.seed(42)
    dates = pd.date_range('2019-01-01', '2023-12-31', freq='B')
    
    # Create realistic returns with occasional crashes
    returns = np.random.randn(len(dates)) * 0.01
    # Add crash periods
    crash_indices = [250, 251, 252, 600, 601, 900, 901]  # Simulate crashes
    returns[crash_indices] = -0.05  # -5% daily returns during crashes
    
    returns_series = pd.Series(returns, index=dates)
    spy_prices = pd.Series(100 * np.exp(returns_series.cumsum()), index=dates)
    spy_returns = spy_prices.pct_change().fillna(0)
    
    # Simulate VIX (higher during crashes)
    vix_series = pd.Series(15 + abs(returns) * 1000, index=dates)
    vix_series[crash_indices] = 50  # High VIX during crashes
    
    # Strategy WITHOUT protection
    unprotected_returns = returns_series.copy()
    unprotected_cumulative = (1 + unprotected_returns).cumprod()
    
    # Strategy WITH protection
    vol_protect = VolatilityProtection()
    protected_returns = []
    exposures = []
    
    for date in dates:
        if len(protected_returns) < 21:  # Need history
            protected_returns.append(returns_series[date])
            exposures.append(1.0)
            continue
            
        adjustments = vol_protect.calculate_combined_adjustment(
            spy_prices=spy_prices[:date],
            spy_returns=spy_returns[:date],
            vix_level=vix_series[date],
            momentum_returns=pd.Series(protected_returns, index=dates[:len(protected_returns)]),
            current_date=date
        )
        
        # Apply protection
        protected_return = returns_series[date] * adjustments['final_exposure']
        protected_returns.append(protected_return)
        exposures.append(adjustments['final_exposure'])
    
    protected_returns_series = pd.Series(protected_returns, index=dates)
    protected_cumulative = (1 + protected_returns_series).cumprod()
    
    # Calculate metrics
    def calc_metrics(returns):
        sharpe = returns.mean() / returns.std() * np.sqrt(252)
        cumulative = (1 + returns).cumprod()
        max_dd = (cumulative / cumulative.cummax() - 1).min()
        total_return = cumulative.iloc[-1] - 1
        return sharpe, max_dd, total_return
    
    unp_sharpe, unp_dd, unp_ret = calc_metrics(unprotected_returns)
    prot_sharpe, prot_dd, prot_ret = calc_metrics(protected_returns_series)
    
    print("\nPerformance Comparison:")
    print("-" * 70)
    print(f"{'Metric':<25} {'Unprotected':<20} {'Protected':<20} {'Improvement'}")
    print("-" * 70)
    print(f"{'Sharpe Ratio':<25} {unp_sharpe:>8.2f}          {prot_sharpe:>8.2f}          {(prot_sharpe/unp_sharpe-1)*100:>6.1f}%")
    print(f"{'Max Drawdown':<25} {unp_dd:>8.1%}          {prot_dd:>8.1%}          {(1-prot_dd/unp_dd)*100:>6.1f}%")
    print(f"{'Total Return':<25} {unp_ret:>8.1%}          {prot_ret:>8.1%}          {(prot_ret-unp_ret)*100:>6.1f}%")
    print(f"{'Avg Exposure':<25} {'100.0%':>13}     {np.mean(exposures):>8.1%}")
    print("-" * 70)


def main():
    """Run all examples"""
    
    print("\n" + "="*70)
    print("VOLATILITY PROTECTION SYSTEM - EXAMPLES")
    print("="*70)
    print("\nThis demonstrates the 5 protection enhancements:")
    print("  1. Volatility Scaling")
    print("  2. Market State Filter")
    print("  3. Crash Indicator")
    print("  4. Dynamic Rebalancing")
    print("  5. Optional Hedging")
    
    # Run examples
    example_1_basic_usage()
    example_2_march_2020_covid_crash()
    example_3_portfolio_integration()
    example_4_backtesting_comparison()
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Review the code in src/strategy/volatility_protection.py")
    print("  2. Read docs/VOLATILITY_PROTECTION_GUIDE.md for integration")
    print("  3. Backtest with your own data")
    print("  4. Tune thresholds to your risk tolerance")
    print("\n")


if __name__ == "__main__":
    main()

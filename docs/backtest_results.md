# Baseline Momentum Strategy Backtest Results

## Test Period: January 1, 2024 - October 31, 2024

### Summary

Successfully implemented and tested a baseline momentum strategy with three different weighting schemes. The strategy selects top 20% momentum stocks from the S&P 500 universe and rebalances monthly.

## Performance Comparison

| Strategy | Total Return | Annual Return | Volatility | Sharpe Ratio | Max Drawdown | Avg Turnover |
|----------|-------------|---------------|------------|--------------|--------------|--------------|
| **Equal Weight** | 35.77% | 41.72% | 16.03% | 2.35 | -7.83% | 28.00% |
| **Value Weight** | 22.02% | 25.48% | 16.73% | 1.28 | -7.97% | 35.68% |
| **Momentum Weight** | **38.65%** | **45.16%** | 16.51% | **2.49** | -8.10% | 29.97% |

### Key Findings

1. **Best Performer: Momentum Weighting**
   - Highest annual return: 45.16%
   - Best risk-adjusted returns: Sharpe ratio of 2.49
   - Moderate turnover: 29.97%
   - Concentrates capital in highest-momentum stocks

2. **Equal Weighting: Strong Performance**
   - Second-best returns: 41.72% annualized
   - Good Sharpe ratio: 2.35
   - Lowest turnover: 28.00%
   - Most diversified approach

3. **Value Weighting: Underperformed**
   - Lowest returns: 25.48% annualized
   - Lowest Sharpe ratio: 1.28
   - Highest turnover: 35.68%
   - Concentrated in high-volume stocks (AAPL, GOOGL, MSFT)

4. **Risk Metrics**
   - All strategies showed similar volatility (~16-17%)
   - Controlled drawdowns (all < -8.1%)
   - High Sharpe ratios indicate excellent risk-adjusted performance

## Strategy Implementation Details

### Universe
- S&P 500 stocks (top 300 for data availability)
- Data quality filters:
  - Minimum price: $5
  - Minimum volume: 100,000 shares/day
  - Minimum history: 252 trading days

### Momentum Calculation
- 12-month lookback period
- Excludes most recent month (22 trading days)
- Selects top 20% by momentum rank

### Portfolio Construction
- Monthly rebalancing
- 15% maximum position size constraint
- Transaction costs: 2 basis points per trade

### Selection Results
- Approximately 15 stocks selected per rebalance (from ~79 eligible)
- Monthly turnover ranged from 13-40%
- Transaction costs: ~$36-$89 per rebalance on $1M portfolio

## Technical Implementation

### Modules Created

1. **src/backtesting/backtest.py**
   - `Backtester`: Main backtesting engine
   - `BacktestResult`: Results container
   - Monthly rebalancing simulation
   - Transaction cost modeling
   - Portfolio value tracking

2. **src/backtesting/metrics.py**
   - `PerformanceMetrics`: Comprehensive metrics calculator
   - Sharpe ratio, Sortino ratio, Calmar ratio
   - Maximum drawdown calculation
   - Annualized returns and volatility

3. **scripts/run_backtest.py**
   - Command-line interface for backtests
   - Strategy comparison functionality
   - Results export to CSV

### Key Features
- ✅ Timezone-aware date handling
- ✅ Rolling window momentum calculation
- ✅ Position size constraints
- ✅ Transaction cost modeling (2 bps)
- ✅ Multiple weighting schemes
- ✅ Comprehensive performance metrics
- ✅ Export functionality

## Issues Resolved

1. **Timezone Handling**
   - Fixed datetime comparison errors between timezone-aware yfinance data and timezone-naive dates
   - Solution: Automatic timezone localization in momentum calculator and backtest engine

2. **Data Availability**
   - Many S&P 500 stocks lack 12-month historical data
   - Increased universe size from 100 to 300 stocks
   - Achieved ~79 stocks with sufficient data for momentum calculation

3. **Portfolio Tracking**
   - Implemented proper daily return calculation during holding periods
   - Fixed date conversion issues in results DataFrame

## Next Steps

### Phase 4: LLM Integration (Steps 13-16)
- Design and test LLM prompts for stock scoring
- Implement LLM-based re-ranking of top momentum stocks
- Add batch processing with rate limiting
- Integrate news data for LLM context

### Phase 5: Enhanced Portfolio Construction (Steps 17-20)
- Implement weight tilting based on LLM scores (η factor from paper)
- Test different tilting parameters
- Compare LLM-enhanced vs baseline performance

### Phase 6: Full Backtesting (Steps 21-24)
- Run validation period backtest (2019-2023)
- Run test period backtest (2024-present)
- Calculate statistical significance of improvements
- Analyze by market conditions

## Conclusion

The baseline momentum strategy shows **excellent performance** with Sharpe ratios above 2.0 for equal and momentum weighting. The momentum-weighted approach achieved the best risk-adjusted returns (Sharpe 2.49, 45.16% annual return), validating the core strategy concept before LLM enhancement.

The framework is now ready for LLM integration to test whether GPT-based stock scoring can further improve performance beyond the already-strong baseline.

---

*Generated: November 5, 2025*
*Test Period: 10 months (Jan-Oct 2024)*
*Initial Capital: $1,000,000*

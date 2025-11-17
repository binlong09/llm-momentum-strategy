# Configuration Guide

This document explains all configuration parameters in `config/config.yaml`.

## Strategy Parameters

### Universe
```yaml
universe: "SP500"
```
Stock universe to trade from. Currently supports S&P 500.

### Momentum Signal
```yaml
momentum_lookback_months: 12
momentum_exclude_recent_month: true
```
- **momentum_lookback_months**: Calculate returns over this period (paper uses 12 months)
- **momentum_exclude_recent_month**: Exclude most recent month to avoid short-term reversal (paper recommendation)

### Portfolio Construction
```yaml
rebalancing_frequency: "monthly"
top_percentile: 0.20
final_portfolio_size: 50
```
- **rebalancing_frequency**: How often to rebalance ("daily", "weekly", "monthly")
- **top_percentile**: Top X% of momentum stocks to send to LLM (0.20 = top 20% ≈ 100 stocks from S&P 500)
- **final_portfolio_size**: Number of stocks in final portfolio after LLM scoring

### Weighting
```yaml
initial_weighting: "value"
max_position_weight: 0.15
weight_tilt_factor: 5.0
```
- **initial_weighting**: Base weighting scheme ("equal" or "value")
- **max_position_weight**: Maximum allocation per stock (0.15 = 15%)
- **weight_tilt_factor**: η parameter for LLM score tilting (higher = more aggressive tilting)
  - Formula: `weight_i × exp(η × LLM_score_i)`

### LLM Configuration
```yaml
llm:
  news_lookback_days: 1
  forecast_horizon_days: 21
  prompt_type: "basic"
  score_range: [0, 1]
  batch_size: 10
  max_retries: 3
  timeout_seconds: 30
```
- **news_lookback_days**: How many days of news to analyze (paper finds 1 day optimal)
- **forecast_horizon_days**: Forecast period for returns (21 days ≈ 1 month)
- **prompt_type**: LLM prompt strategy ("basic" or "advanced")
- **score_range**: Output range for LLM scores (normalized to [-1, 1] internally)
- **batch_size**: Process N stocks at a time (manages API rate limits)
- **max_retries**: Retry failed API calls this many times
- **timeout_seconds**: Max time to wait for LLM response

### Transaction Costs
```yaml
transaction_cost_bps: 2
```
Transaction cost in basis points (2 bps = 0.02% per trade)

## Backtesting Configuration

```yaml
backtesting:
  validation_start: "2019-10-01"
  validation_end: "2023-12-31"
  test_start: "2024-01-01"
  test_end: "2025-03-31"

  metrics:
    - "sharpe_ratio"
    - "sortino_ratio"
    - "annual_return"
    - "volatility"
    - "max_drawdown"
    - "calmar_ratio"
    - "turnover"
```
- **Dates**: Define validation and test periods (use YYYY-MM-DD format)
- **Metrics**: Performance metrics to calculate

## Data Sources

```yaml
data_sources:
  price_data: "alpha_vantage"

  news_sources:
    rss_feeds: true
    newsapi: false
    alpha_vantage_sentiment: true

  risk_free_rate_source: "fred"
```
- **price_data**: Stock price source ("alpha_vantage" or "yfinance")
- **news_sources**: Multiple sources can be enabled
  - `rss_feeds`: Free RSS feeds from financial sites
  - `newsapi`: NewsAPI.org (requires API key)
  - `alpha_vantage_sentiment`: Alpha Vantage NEWS_SENTIMENT endpoint
- **risk_free_rate_source**: Source for risk-free rate (for Sharpe ratio)

## Caching

```yaml
cache:
  enabled: true
  cache_dir: "data/raw"
  price_cache_days: 1
  news_cache_hours: 6
```
- **enabled**: Enable/disable caching
- **cache_dir**: Directory for cached data
- **price_cache_days**: Refresh price data after N days
- **news_cache_hours**: Refresh news data after N hours

## Logging

```yaml
logging:
  level: "INFO"
  log_file: "logs/strategy.log"
  console_output: true
```
- **level**: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- **log_file**: Path to log file
- **console_output**: Also print logs to console

## Key Parameters from Paper

Based on "ChatGPT in Systematic Investing" validation results:

| Parameter | Optimal Value | Notes |
|-----------|---------------|-------|
| News lookback | 1 day | Shorter is better |
| Forecast horizon | 21 days | ~1 month rebalancing |
| Momentum period | 12 months | Standard momentum |
| Weight tilt η | 5.0 | Moderate tilting |
| Top percentile | 20% | Top 2 deciles |
| Max position | 15% | Risk management |

## Modifying Parameters

To experiment with different strategies:

1. Edit `config/config.yaml`
2. Run validation: `python scripts/validate_config.py`
3. Run backtests with new parameters
4. Compare performance metrics

**Important**: Always validate config after changes!

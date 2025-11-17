"""
Performance Analytics - Calculate portfolio performance metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from loguru import logger
import yfinance as yf


class PerformanceAnalytics:
    """Calculate and track portfolio performance metrics."""

    def __init__(self):
        pass

    def calculate_metrics(
        self,
        snapshots_df: pd.DataFrame,
        benchmark_symbol: str = 'SPY'
    ) -> Dict:
        """
        Calculate comprehensive performance metrics.

        Args:
            snapshots_df: Historical portfolio snapshots
            benchmark_symbol: Benchmark ticker (default SPY for S&P 500)

        Returns:
            Dictionary of performance metrics
        """
        if len(snapshots_df) < 2:
            return {
                'error': 'Insufficient data',
                'min_days_required': 2,
                'current_days': len(snapshots_df)
            }

        # Ensure sorted by date
        snapshots_df = snapshots_df.sort_values('date')
        snapshots_df['date'] = pd.to_datetime(snapshots_df['date'])

        # Calculate returns
        snapshots_df['daily_return'] = snapshots_df['total_value'].pct_change()

        # Total return
        start_value = snapshots_df.iloc[0]['total_value']
        end_value = snapshots_df.iloc[-1]['total_value']
        total_return = (end_value - start_value) / start_value

        # Annualized return
        num_days = (snapshots_df.iloc[-1]['date'] - snapshots_df.iloc[0]['date']).days
        if num_days > 0:
            annualized_return = ((1 + total_return) ** (365 / num_days)) - 1
        else:
            annualized_return = 0

        # Volatility (annualized)
        daily_returns = snapshots_df['daily_return'].dropna()
        if len(daily_returns) > 1:
            daily_volatility = daily_returns.std()
            annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days
        else:
            annualized_volatility = 0

        # Sharpe ratio (assume 4% risk-free rate)
        risk_free_rate = 0.04
        if annualized_volatility > 0:
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
        else:
            sharpe_ratio = 0

        # Maximum drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win rate (percentage of positive days)
        if len(daily_returns) > 0:
            win_rate = (daily_returns > 0).sum() / len(daily_returns)
        else:
            win_rate = 0

        # Best and worst days
        if len(daily_returns) > 0:
            best_day = daily_returns.max()
            worst_day = daily_returns.min()
        else:
            best_day = worst_day = 0

        metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'best_day': best_day,
            'worst_day': worst_day,
            'start_value': start_value,
            'end_value': end_value,
            'num_days': num_days,
            'num_data_points': len(snapshots_df)
        }

        # Fetch benchmark performance
        try:
            benchmark_metrics = self._calculate_benchmark_performance(
                snapshots_df, benchmark_symbol
            )
            metrics['benchmark'] = benchmark_metrics
            metrics['alpha'] = annualized_return - benchmark_metrics['annualized_return']
        except Exception as e:
            logger.warning(f"Could not fetch benchmark data: {e}")
            metrics['benchmark'] = None
            metrics['alpha'] = None

        return metrics

    def _calculate_benchmark_performance(
        self,
        snapshots_df: pd.DataFrame,
        benchmark_symbol: str
    ) -> Dict:
        """Calculate benchmark performance for comparison."""

        start_date = snapshots_df.iloc[0]['date']
        end_date = snapshots_df.iloc[-1]['date']

        # Fetch benchmark data
        benchmark = yf.Ticker(benchmark_symbol)
        hist = benchmark.history(start=start_date, end=end_date + timedelta(days=1))

        if len(hist) < 2:
            raise ValueError("Insufficient benchmark data")

        # Calculate benchmark returns
        start_price = hist.iloc[0]['Close']
        end_price = hist.iloc[-1]['Close']
        total_return = (end_price - start_price) / start_price

        # Annualized return
        num_days = (end_date - start_date).days
        if num_days > 0:
            annualized_return = ((1 + total_return) ** (365 / num_days)) - 1
        else:
            annualized_return = 0

        # Daily returns and volatility
        hist['daily_return'] = hist['Close'].pct_change()
        daily_returns = hist['daily_return'].dropna()

        if len(daily_returns) > 1:
            daily_volatility = daily_returns.std()
            annualized_volatility = daily_volatility * np.sqrt(252)
        else:
            annualized_volatility = 0

        # Max drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            'symbol': benchmark_symbol,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'max_drawdown': max_drawdown,
            'start_price': start_price,
            'end_price': end_price
        }

    def calculate_stock_contribution(
        self,
        holdings_history_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate each stock's contribution to portfolio performance.

        Args:
            holdings_history_df: Historical holdings data

        Returns:
            DataFrame with contribution analysis
        """
        if len(holdings_history_df) == 0:
            return pd.DataFrame()

        # Group by symbol
        contributions = []

        for symbol in holdings_history_df['symbol'].unique():
            stock_data = holdings_history_df[
                holdings_history_df['symbol'] == symbol
            ].sort_values('date')

            if len(stock_data) < 2:
                continue

            # Calculate return for this stock
            first_value = stock_data.iloc[0]['current_value']
            last_value = stock_data.iloc[-1]['current_value']

            if first_value > 0:
                stock_return = (last_value - first_value) / first_value
                contribution = last_value - first_value  # Dollar contribution
            else:
                stock_return = 0
                contribution = 0

            # Average weight in portfolio
            avg_weight = stock_data['current_weight'].mean() if 'current_weight' in stock_data else 0

            contributions.append({
                'symbol': symbol,
                'total_return': stock_return,
                'dollar_contribution': contribution,
                'avg_weight': avg_weight,
                'days_held': len(stock_data),
                'first_value': first_value,
                'last_value': last_value
            })

        contributions_df = pd.DataFrame(contributions)

        # Sort by dollar contribution
        contributions_df = contributions_df.sort_values(
            'dollar_contribution', ascending=False
        )

        return contributions_df

    def calculate_risk_metrics(
        self,
        holdings_df: pd.DataFrame,
        holdings_history_df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Calculate portfolio risk metrics.

        Args:
            holdings_df: Current holdings
            holdings_history_df: Historical holdings (optional)

        Returns:
            Dictionary of risk metrics
        """
        metrics = {}

        # Concentration risk
        if 'current_weight' in holdings_df.columns:
            max_weight = holdings_df['current_weight'].max()
            top5_weight = holdings_df.nlargest(5, 'current_weight')['current_weight'].sum()
            herfindahl_index = (holdings_df['current_weight'] ** 2).sum()

            metrics['max_position_weight'] = max_weight
            metrics['top5_concentration'] = top5_weight
            metrics['herfindahl_index'] = herfindahl_index
            metrics['effective_num_stocks'] = 1 / herfindahl_index if herfindahl_index > 0 else 0

        # Sector concentration (if sector data available)
        # This would require additional data

        # Turnover (if historical data available)
        if holdings_history_df is not None and len(holdings_history_df) > 0:
            # Calculate monthly turnover
            # This is a simplified version
            unique_dates = holdings_history_df['date'].unique()
            if len(unique_dates) >= 2:
                # Get stocks from two most recent snapshots
                recent_dates = sorted(unique_dates)[-2:]
                old_stocks = set(
                    holdings_history_df[holdings_history_df['date'] == recent_dates[0]]['symbol']
                )
                new_stocks = set(
                    holdings_history_df[holdings_history_df['date'] == recent_dates[1]]['symbol']
                )

                stocks_changed = len(old_stocks.symmetric_difference(new_stocks))
                total_stocks = max(len(old_stocks), len(new_stocks))

                if total_stocks > 0:
                    metrics['recent_turnover'] = stocks_changed / total_stocks
                else:
                    metrics['recent_turnover'] = 0

        return metrics

    def generate_performance_report(
        self,
        metrics: Dict,
        period_name: str = "Portfolio"
    ) -> str:
        """
        Generate formatted performance report.

        Args:
            metrics: Performance metrics dictionary
            period_name: Name of period (e.g., "30-Day", "90-Day")

        Returns:
            Formatted report string
        """
        if 'error' in metrics:
            return f"Cannot generate report: {metrics['error']}"

        report = []
        report.append("=" * 80)
        report.append(f"{period_name} PERFORMANCE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        report.append("=" * 80)
        report.append("")

        # Returns
        report.append("📈 RETURNS")
        report.append("-" * 80)
        report.append(f"  Total Return:      {metrics['total_return']*100:>8.2f}%")
        report.append(f"  Annualized Return: {metrics['annualized_return']*100:>8.2f}%")
        report.append(f"  Start Value:       ${metrics['start_value']:>12,.2f}")
        report.append(f"  End Value:         ${metrics['end_value']:>12,.2f}")
        report.append(f"  Gain/Loss:         ${(metrics['end_value'] - metrics['start_value']):>12,.2f}")
        report.append("")

        # Risk
        report.append("📊 RISK METRICS")
        report.append("-" * 80)
        report.append(f"  Volatility (Annual): {metrics['annualized_volatility']*100:>6.2f}%")
        report.append(f"  Sharpe Ratio:        {metrics['sharpe_ratio']:>6.2f}")
        report.append(f"  Max Drawdown:        {metrics['max_drawdown']*100:>6.2f}%")
        report.append(f"  Win Rate:            {metrics['win_rate']*100:>6.2f}%")
        report.append(f"  Best Day:            {metrics['best_day']*100:>6.2f}%")
        report.append(f"  Worst Day:           {metrics['worst_day']*100:>6.2f}%")
        report.append("")

        # Benchmark comparison
        if metrics.get('benchmark'):
            bench = metrics['benchmark']
            report.append(f"📊 BENCHMARK COMPARISON ({bench['symbol']})")
            report.append("-" * 80)
            report.append(f"  Portfolio Return:  {metrics['annualized_return']*100:>8.2f}%")
            report.append(f"  Benchmark Return:  {bench['annualized_return']*100:>8.2f}%")
            report.append(f"  Alpha:             {metrics['alpha']*100:>8.2f}%")
            report.append(f"  Portfolio Vol:     {metrics['annualized_volatility']*100:>8.2f}%")
            report.append(f"  Benchmark Vol:     {bench['annualized_volatility']*100:>8.2f}%")
            report.append("")

        # Period info
        report.append("📅 PERIOD INFORMATION")
        report.append("-" * 80)
        report.append(f"  Days Tracked:      {metrics['num_days']}")
        report.append(f"  Data Points:       {metrics['num_data_points']}")
        report.append("")

        return "\n".join(report)

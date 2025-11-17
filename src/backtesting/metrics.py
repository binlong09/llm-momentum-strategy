"""
Performance Metrics Calculator
Calculates standard financial performance metrics for backtesting.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from loguru import logger


class PerformanceMetrics:
    """
    Calculates performance metrics for trading strategies.

    Metrics:
    - Total return
    - Annualized return
    - Volatility
    - Sharpe ratio
    - Sortino ratio
    - Maximum drawdown
    - Calmar ratio
    """

    def __init__(self, risk_free_rate: float = 0.04):
        """
        Initialize metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate (default: 4%)
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = 252

    def total_return(self, portfolio_value: pd.Series) -> float:
        """
        Calculate total return.

        Args:
            portfolio_value: Time series of portfolio values

        Returns:
            Total return as decimal
        """
        if portfolio_value.empty or len(portfolio_value) < 2:
            return 0.0

        initial_value = portfolio_value.iloc[0]
        final_value = portfolio_value.iloc[-1]

        if initial_value <= 0:
            return 0.0

        return (final_value / initial_value) - 1

    def annualized_return(
        self,
        daily_returns: pd.Series,
        periods_per_year: Optional[int] = None
    ) -> float:
        """
        Calculate annualized return.

        Args:
            daily_returns: Time series of daily returns
            periods_per_year: Periods in a year (default: 252 for daily)

        Returns:
            Annualized return as decimal
        """
        if daily_returns.empty:
            return 0.0

        if periods_per_year is None:
            periods_per_year = self.trading_days_per_year

        # Compound return
        cumulative_return = (1 + daily_returns).prod() - 1

        # Annualize
        num_periods = len(daily_returns)
        years = num_periods / periods_per_year

        if years <= 0:
            return 0.0

        annualized = (1 + cumulative_return) ** (1 / years) - 1

        return annualized

    def annual_volatility(
        self,
        daily_returns: pd.Series,
        periods_per_year: Optional[int] = None
    ) -> float:
        """
        Calculate annualized volatility.

        Args:
            daily_returns: Time series of daily returns
            periods_per_year: Periods in a year (default: 252)

        Returns:
            Annualized volatility as decimal
        """
        if daily_returns.empty or len(daily_returns) < 2:
            return 0.0

        if periods_per_year is None:
            periods_per_year = self.trading_days_per_year

        # Daily volatility
        daily_vol = daily_returns.std()

        # Annualize
        annual_vol = daily_vol * np.sqrt(periods_per_year)

        return annual_vol

    def sharpe_ratio(
        self,
        daily_returns: pd.Series,
        risk_free_rate: Optional[float] = None,
        periods_per_year: Optional[int] = None
    ) -> float:
        """
        Calculate Sharpe ratio.

        Sharpe = (Return - RiskFreeRate) / Volatility

        Args:
            daily_returns: Time series of daily returns
            risk_free_rate: Annual risk-free rate (default: from config)
            periods_per_year: Periods in a year (default: 252)

        Returns:
            Sharpe ratio
        """
        if daily_returns.empty or len(daily_returns) < 2:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        if periods_per_year is None:
            periods_per_year = self.trading_days_per_year

        ann_return = self.annualized_return(daily_returns, periods_per_year)
        ann_vol = self.annual_volatility(daily_returns, periods_per_year)

        if ann_vol == 0:
            return 0.0

        sharpe = (ann_return - risk_free_rate) / ann_vol

        return sharpe

    def sortino_ratio(
        self,
        daily_returns: pd.Series,
        risk_free_rate: Optional[float] = None,
        periods_per_year: Optional[int] = None
    ) -> float:
        """
        Calculate Sortino ratio (only penalizes downside volatility).

        Args:
            daily_returns: Time series of daily returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Periods in a year

        Returns:
            Sortino ratio
        """
        if daily_returns.empty or len(daily_returns) < 2:
            return 0.0

        if risk_free_rate is None:
            risk_free_rate = self.risk_free_rate

        if periods_per_year is None:
            periods_per_year = self.trading_days_per_year

        ann_return = self.annualized_return(daily_returns, periods_per_year)

        # Downside deviation (only negative returns)
        negative_returns = daily_returns[daily_returns < 0]

        if len(negative_returns) == 0:
            # No negative returns - infinite Sortino
            return np.inf

        downside_std = negative_returns.std()
        downside_vol = downside_std * np.sqrt(periods_per_year)

        if downside_vol == 0:
            return 0.0

        sortino = (ann_return - risk_free_rate) / downside_vol

        return sortino

    def max_drawdown(self, portfolio_value: pd.Series) -> float:
        """
        Calculate maximum drawdown.

        Args:
            portfolio_value: Time series of portfolio values

        Returns:
            Maximum drawdown as negative decimal
        """
        if portfolio_value.empty or len(portfolio_value) < 2:
            return 0.0

        # Calculate running maximum
        running_max = portfolio_value.expanding().max()

        # Calculate drawdown at each point
        drawdown = (portfolio_value - running_max) / running_max

        # Maximum drawdown (most negative)
        max_dd = drawdown.min()

        return max_dd

    def calmar_ratio(
        self,
        daily_returns: pd.Series,
        portfolio_value: pd.Series
    ) -> float:
        """
        Calculate Calmar ratio.

        Calmar = Annualized Return / |Max Drawdown|

        Args:
            daily_returns: Time series of daily returns
            portfolio_value: Time series of portfolio values

        Returns:
            Calmar ratio
        """
        ann_return = self.annualized_return(daily_returns)
        max_dd = self.max_drawdown(portfolio_value)

        if max_dd == 0:
            return 0.0

        calmar = ann_return / abs(max_dd)

        return calmar

    def calculate_all_metrics(
        self,
        daily_returns: pd.Series,
        portfolio_value: pd.Series
    ) -> Dict:
        """
        Calculate all performance metrics.

        Args:
            daily_returns: Time series of daily returns
            portfolio_value: Time series of portfolio values

        Returns:
            Dictionary with all metrics
        """
        metrics = {}

        try:
            metrics['total_return'] = self.total_return(portfolio_value)
            metrics['annual_return'] = self.annualized_return(daily_returns)
            metrics['annual_volatility'] = self.annual_volatility(daily_returns)
            metrics['sharpe_ratio'] = self.sharpe_ratio(daily_returns)
            metrics['sortino_ratio'] = self.sortino_ratio(daily_returns)
            metrics['max_drawdown'] = self.max_drawdown(portfolio_value)
            metrics['calmar_ratio'] = self.calmar_ratio(daily_returns, portfolio_value)

            # Additional statistics
            metrics['best_day'] = daily_returns.max() if not daily_returns.empty else 0.0
            metrics['worst_day'] = daily_returns.min() if not daily_returns.empty else 0.0
            metrics['positive_days'] = (daily_returns > 0).sum() if not daily_returns.empty else 0
            metrics['negative_days'] = (daily_returns < 0).sum() if not daily_returns.empty else 0
            metrics['win_rate'] = (
                metrics['positive_days'] / len(daily_returns)
                if not daily_returns.empty and len(daily_returns) > 0
                else 0.0
            )

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")

        return metrics

    def format_metrics_report(self, metrics: Dict) -> str:
        """
        Format metrics as readable report.

        Args:
            metrics: Dictionary of metrics

        Returns:
            Formatted string
        """
        report_parts = [
            "=" * 60,
            "PERFORMANCE METRICS",
            "=" * 60,
            "",
            "Returns:",
            f"  Total Return:          {metrics.get('total_return', 0):>8.2%}",
            f"  Annualized Return:     {metrics.get('annual_return', 0):>8.2%}",
            "",
            "Risk:",
            f"  Annual Volatility:     {metrics.get('annual_volatility', 0):>8.2%}",
            f"  Maximum Drawdown:      {metrics.get('max_drawdown', 0):>8.2%}",
            "",
            "Risk-Adjusted Performance:",
            f"  Sharpe Ratio:          {metrics.get('sharpe_ratio', 0):>8.2f}",
            f"  Sortino Ratio:         {metrics.get('sortino_ratio', 0):>8.2f}",
            f"  Calmar Ratio:          {metrics.get('calmar_ratio', 0):>8.2f}",
            "",
            "Daily Statistics:",
            f"  Best Day:              {metrics.get('best_day', 0):>8.2%}",
            f"  Worst Day:             {metrics.get('worst_day', 0):>8.2%}",
            f"  Win Rate:              {metrics.get('win_rate', 0):>8.2%}",
            f"  Positive Days:         {metrics.get('positive_days', 0):>8}",
            f"  Negative Days:         {metrics.get('negative_days', 0):>8}",
            "",
            "=" * 60
        ]

        return "\n".join(report_parts)


def main():
    """Test metrics calculator."""
    # Create sample returns
    np.random.seed(42)

    # Simulate daily returns (slight positive drift, some volatility)
    n_days = 252  # 1 year
    daily_returns = pd.Series(
        np.random.normal(0.0005, 0.01, n_days),  # 0.05% daily return, 1% daily vol
        index=pd.date_range('2023-01-01', periods=n_days, freq='B')
    )

    # Calculate portfolio value
    portfolio_value = (1 + daily_returns).cumprod() * 1000000

    # Calculate metrics
    calculator = PerformanceMetrics()
    metrics = calculator.calculate_all_metrics(daily_returns, portfolio_value)

    # Display report
    report = calculator.format_metrics_report(metrics)
    print("\n" + report)

    # Show individual metrics
    logger.info("\nDetailed Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'ratio' in key.lower() or 'rate' in key.lower():
                logger.info(f"  {key}: {value:.4f}")
            else:
                logger.info(f"  {key}: {value:.2%}")
        else:
            logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()

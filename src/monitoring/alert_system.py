"""
Alert System - Detect and prioritize portfolio alerts
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger


class AlertSystem:
    """Generate alerts based on price movements, news, and other signals."""

    def __init__(self):
        self.alert_thresholds = {
            'critical_drop': -0.15,  # -15% or worse
            'warning_drop': -0.10,   # -10% to -15%
            'significant_drop': -0.05,  # -5% to -10%
            'critical_gain': 0.20,   # +20% or more (take profit consideration)
            'significant_gain': 0.10  # +10% to +20%
        }

    def generate_alerts(
        self,
        holdings_df: pd.DataFrame,
        news_monitoring_df: Optional[pd.DataFrame] = None,
        previous_snapshot: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Generate comprehensive alerts for portfolio.

        Args:
            holdings_df: Current holdings with prices
            news_monitoring_df: News monitoring results
            previous_snapshot: Previous day's holdings for comparison

        Returns:
            DataFrame of alerts sorted by priority
        """
        alerts = []

        # Price-based alerts
        if 'price_change_pct' in holdings_df.columns:
            price_alerts = self._generate_price_alerts(holdings_df)
            alerts.extend(price_alerts)

        # News-based alerts
        if news_monitoring_df is not None:
            news_alerts = self._generate_news_alerts(news_monitoring_df)
            alerts.extend(news_alerts)

        # Position size alerts
        if 'current_weight' in holdings_df.columns:
            position_alerts = self._generate_position_alerts(holdings_df)
            alerts.extend(position_alerts)

        # Momentum breakdown alerts (if we have historical data)
        if previous_snapshot is not None:
            momentum_alerts = self._generate_momentum_alerts(
                holdings_df, previous_snapshot
            )
            alerts.extend(momentum_alerts)

        # Convert to DataFrame and sort
        if not alerts:
            return pd.DataFrame(columns=[
                'symbol', 'alert_type', 'severity', 'message', 'action', 'timestamp'
            ])

        alerts_df = pd.DataFrame(alerts)

        # Sort by severity priority
        severity_priority = {'critical': 0, 'warning': 1, 'info': 2}
        alerts_df['_priority'] = alerts_df['severity'].map(severity_priority)
        alerts_df = alerts_df.sort_values(['_priority', 'timestamp'], ascending=[True, False])
        alerts_df = alerts_df.drop('_priority', axis=1)

        logger.info(f"Generated {len(alerts_df)} alerts")

        return alerts_df

    def _generate_price_alerts(self, holdings_df: pd.DataFrame) -> List[Dict]:
        """Generate alerts based on price movements."""
        alerts = []

        for _, row in holdings_df.iterrows():
            symbol = row['symbol']
            price_change = row.get('price_change_pct', 0) / 100  # Convert to decimal

            # Critical drop
            if price_change <= self.alert_thresholds['critical_drop']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'price_drop_critical',
                    'severity': 'critical',
                    'message': f"{symbol} down {price_change*100:.1f}% - Critical drop detected",
                    'action': 'Review news immediately. Consider selling if fundamentals deteriorated.',
                    'value': price_change,
                    'timestamp': datetime.now()
                })

            # Warning drop
            elif price_change <= self.alert_thresholds['warning_drop']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'price_drop_warning',
                    'severity': 'warning',
                    'message': f"{symbol} down {price_change*100:.1f}% - Significant drop",
                    'action': 'Monitor closely. Check news and analyst updates.',
                    'value': price_change,
                    'timestamp': datetime.now()
                })

            # Significant drop (info level)
            elif price_change <= self.alert_thresholds['significant_drop']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'price_drop',
                    'severity': 'info',
                    'message': f"{symbol} down {price_change*100:.1f}%",
                    'action': 'Normal volatility. Monitor if continues.',
                    'value': price_change,
                    'timestamp': datetime.now()
                })

            # Critical gain (potential take profit)
            elif price_change >= self.alert_thresholds['critical_gain']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'price_gain_critical',
                    'severity': 'info',
                    'message': f"{symbol} up {price_change*100:.1f}% - Strong gain",
                    'action': 'Consider taking partial profits. Wait for monthly rebalance unless overextended.',
                    'value': price_change,
                    'timestamp': datetime.now()
                })

            # Significant gain
            elif price_change >= self.alert_thresholds['significant_gain']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'price_gain',
                    'severity': 'info',
                    'message': f"{symbol} up {price_change*100:.1f}%",
                    'action': 'Momentum working. Hold until monthly rebalance.',
                    'value': price_change,
                    'timestamp': datetime.now()
                })

        return alerts

    def _generate_news_alerts(self, news_df: pd.DataFrame) -> List[Dict]:
        """Generate alerts based on news monitoring."""
        alerts = []

        for _, row in news_df.iterrows():
            symbol = row['symbol']
            alert_level = row['alert_level']

            if alert_level == 'critical':
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'news_critical',
                    'severity': 'critical',
                    'message': f"{symbol}: {row['summary']}",
                    'action': f"URGENT: Review immediately. Red flags: {', '.join(row['red_flags'])}",
                    'value': None,
                    'timestamp': datetime.now()
                })

            elif alert_level == 'warning':
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'news_warning',
                    'severity': 'warning',
                    'message': f"{symbol}: {row['summary']}",
                    'action': 'Review news and consider impact on thesis.',
                    'value': None,
                    'timestamp': datetime.now()
                })

            elif alert_level == 'info' and row['sentiment'] in ['positive', 'very_positive']:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'news_positive',
                    'severity': 'info',
                    'message': f"{symbol}: {row['summary']}",
                    'action': 'Positive catalyst. Monitor momentum continuation.',
                    'value': None,
                    'timestamp': datetime.now()
                })

        return alerts

    def _generate_position_alerts(self, holdings_df: pd.DataFrame) -> List[Dict]:
        """Generate alerts based on position sizes."""
        alerts = []

        for _, row in holdings_df.iterrows():
            symbol = row['symbol']
            weight = row.get('current_weight', 0)

            # Concentrated position (>20% of portfolio)
            if weight > 0.20:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'concentration',
                    'severity': 'warning',
                    'message': f"{symbol} is {weight*100:.1f}% of portfolio - Highly concentrated",
                    'action': 'Consider reducing concentration risk at next rebalance.',
                    'value': weight,
                    'timestamp': datetime.now()
                })

            # Very large position (>30%)
            elif weight > 0.30:
                alerts.append({
                    'symbol': symbol,
                    'alert_type': 'concentration_critical',
                    'severity': 'critical',
                    'message': f"{symbol} is {weight*100:.1f}% of portfolio - EXTREME concentration",
                    'action': 'URGENT: Reduce position size to manage risk.',
                    'value': weight,
                    'timestamp': datetime.now()
                })

        return alerts

    def _generate_momentum_alerts(
        self,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame
    ) -> List[Dict]:
        """Generate alerts for momentum breakdown."""
        alerts = []

        # Compare current vs previous for momentum signals
        for symbol in current_df['symbol']:
            current_row = current_df[current_df['symbol'] == symbol]
            if len(current_row) == 0:
                continue

            # Check if stock existed previously
            prev_row = previous_df[previous_df['symbol'] == symbol]
            if len(prev_row) == 0:
                continue  # New position, no comparison

            # Check for sustained decline (would need multi-day data)
            # This is a placeholder for future enhancement
            pass

        return alerts

    def get_critical_actions(self, alerts_df: pd.DataFrame) -> pd.DataFrame:
        """Get alerts that require immediate action."""
        return alerts_df[alerts_df['severity'] == 'critical']

    def summarize_alerts(self, alerts_df: pd.DataFrame) -> Dict:
        """Generate alert summary statistics."""
        if len(alerts_df) == 0:
            return {
                'total_alerts': 0,
                'critical': 0,
                'warnings': 0,
                'info': 0,
                'requires_action': False
            }

        summary = {
            'total_alerts': len(alerts_df),
            'critical': len(alerts_df[alerts_df['severity'] == 'critical']),
            'warnings': len(alerts_df[alerts_df['severity'] == 'warning']),
            'info': len(alerts_df[alerts_df['severity'] == 'info']),
            'requires_action': len(alerts_df[alerts_df['severity'] == 'critical']) > 0
        }

        # Group by type
        alert_types = alerts_df['alert_type'].value_counts().to_dict()
        summary['by_type'] = alert_types

        return summary

    def format_alert_message(self, alert: Dict) -> str:
        """Format a single alert for display."""
        severity_emoji = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }

        emoji = severity_emoji.get(alert['severity'], '•')

        message = f"{emoji} [{alert['severity'].upper()}] {alert['message']}\n"
        message += f"   Action: {alert['action']}"

        return message

"""
Daily Monitor - Automated portfolio monitoring system
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from pathlib import Path

from src.monitoring import PortfolioTracker, NewsMonitor, AlertSystem, PerformanceAnalytics
from src.utils.robinhood_export import parse_robinhood_holdings
from .email_notifier import EmailNotifier


class DailyMonitor:
    """Automated daily portfolio monitoring with notifications."""

    def __init__(
        self,
        email_config: Optional[Dict] = None,
        robinhood_csv_path: Optional[str] = None
    ):
        """
        Initialize daily monitor.

        Args:
            email_config: Dict with 'sender_email', 'sender_password', 'recipient_email'
            robinhood_csv_path: Path to Robinhood CSV (optional, can use snapshots)
        """
        self.tracker = PortfolioTracker()
        self.news_monitor = NewsMonitor()
        self.alert_system = AlertSystem()
        self.analytics = PerformanceAnalytics()

        # Email notifier
        if email_config:
            self.email_notifier = EmailNotifier(**email_config)
        else:
            self.email_notifier = None
            logger.warning("Email not configured. Run in dry-run mode.")

        self.robinhood_csv_path = robinhood_csv_path

    def run_daily_check(
        self,
        use_llm_for_news: bool = False,
        send_email: bool = True,
        send_critical_alerts: bool = True
    ) -> Dict:
        """
        Run complete daily monitoring routine.

        Args:
            use_llm_for_news: Whether to use LLM for news sentiment (slower but better)
            send_email: Send daily summary email
            send_critical_alerts: Send immediate emails for critical alerts

        Returns:
            Dict with monitoring results
        """
        logger.info("="*80)
        logger.info(f"DAILY MONITORING - {datetime.now().strftime('%Y-%m-%d %I:%M %p ET')}")
        logger.info("="*80)

        results = {}

        try:
            # Step 1: Load portfolio
            logger.info("\n1️⃣ Loading portfolio...")
            holdings_df = self._load_portfolio()

            if holdings_df is None or len(holdings_df) == 0:
                logger.error("No portfolio data available")
                return {'error': 'No portfolio data'}

            logger.success(f"  Loaded {len(holdings_df)} holdings")
            results['num_holdings'] = len(holdings_df)

            # Step 2: Update prices
            logger.info("\n2️⃣ Updating prices...")
            holdings_df = self.tracker.update_prices(holdings_df)
            results['holdings'] = holdings_df

            # Step 3: Take snapshot
            logger.info("\n3️⃣ Taking portfolio snapshot...")
            snapshot = self.tracker.snapshot_portfolio(holdings_df, source="automated")

            portfolio_value = snapshot['total_value']
            results['portfolio_value'] = portfolio_value
            logger.success(f"  Portfolio value: ${portfolio_value:,.2f}")

            # Calculate daily change
            daily_stats = self.tracker.calculate_daily_change()
            if daily_stats:
                daily_change = daily_stats['change']
                daily_change_pct = daily_stats['change_pct']
                results['daily_change'] = daily_change
                results['daily_change_pct'] = daily_change_pct
                logger.info(f"  Daily change: ${daily_change:+,.2f} ({daily_change_pct:+.2f}%)")
            else:
                daily_change = 0
                daily_change_pct = 0
                results['daily_change'] = 0
                results['daily_change_pct'] = 0

            # Step 4: Scan news
            logger.info("\n4️⃣ Scanning news...")
            symbols = holdings_df['symbol'].tolist()
            news_df = self.news_monitor.monitor_holdings(
                symbols=symbols,
                lookback_days=1,
                use_llm=use_llm_for_news
            )
            results['news'] = news_df

            critical_news = len(news_df[news_df['alert_level'] == 'critical'])
            warnings = len(news_df[news_df['alert_level'] == 'warning'])
            logger.info(f"  Critical news: {critical_news}, Warnings: {warnings}")

            # Step 5: Generate alerts
            logger.info("\n5️⃣ Generating alerts...")
            alerts_df = self.alert_system.generate_alerts(
                holdings_df=holdings_df,
                news_monitoring_df=news_df
            )
            results['alerts'] = alerts_df

            summary = self.alert_system.summarize_alerts(alerts_df)
            logger.info(f"  Total alerts: {summary['total_alerts']}")
            logger.info(f"  Critical: {summary['critical']}, Warnings: {summary['warnings']}")

            # Step 6: Identify top movers
            logger.info("\n6️⃣ Identifying top movers...")
            top_movers = self._get_top_movers(holdings_df)
            results['top_movers'] = top_movers

            if top_movers['up']:
                logger.info(f"  Top gainer: {top_movers['up'][0][0]} (+{top_movers['up'][0][1]:.2f}%)")
            if top_movers['down']:
                logger.info(f"  Top decliner: {top_movers['down'][0][0]} ({top_movers['down'][0][1]:.2f}%)")

            # Step 7: Send critical alerts immediately
            if send_critical_alerts and self.email_notifier:
                critical_alerts = self.alert_system.get_critical_actions(alerts_df)
                if len(critical_alerts) > 0:
                    logger.warning(f"\n⚠️ Sending {len(critical_alerts)} critical alerts...")
                    for _, alert in critical_alerts.iterrows():
                        # Get evidence URL if available
                        evidence_url = None
                        if 'symbol' in alert:
                            news_row = news_df[news_df['symbol'] == alert['symbol']]
                            if len(news_row) > 0 and 'latest_url' in news_row.iloc[0]:
                                evidence_url = news_row.iloc[0]['latest_url']

                        self.email_notifier.send_critical_alert(
                            symbol=alert['symbol'],
                            message=alert['message'],
                            action=alert['action'],
                            evidence_url=evidence_url
                        )

            # Step 8: Send daily summary email
            if send_email and self.email_notifier:
                logger.info("\n7️⃣ Sending daily summary email...")
                success = self.email_notifier.send_daily_summary(
                    portfolio_value=portfolio_value,
                    daily_change=daily_change,
                    daily_change_pct=daily_change_pct,
                    alerts_df=alerts_df,
                    news_df=news_df,
                    top_movers=top_movers
                )

                if success:
                    logger.success("  Daily summary email sent")
                else:
                    logger.warning("  Failed to send email")

            # Final summary
            logger.info("\n" + "="*80)
            if summary['critical'] > 0:
                logger.warning(f"⚠️ ACTION REQUIRED: {summary['critical']} critical alerts")
            else:
                logger.success("✅ No critical alerts - portfolio healthy")

            logger.info("="*80)

            results['success'] = True
            return results

        except Exception as e:
            logger.error(f"Daily monitoring failed: {e}")
            import traceback
            traceback.print_exc()
            results['success'] = False
            results['error'] = str(e)
            return results

    def _load_portfolio(self) -> Optional[pd.DataFrame]:
        """Load portfolio from Robinhood CSV or latest snapshot."""

        # Try Robinhood CSV first
        if self.robinhood_csv_path and Path(self.robinhood_csv_path).exists():
            try:
                holdings_df = parse_robinhood_holdings(self.robinhood_csv_path)
                logger.info(f"  Loaded from Robinhood CSV: {self.robinhood_csv_path}")
                return holdings_df
            except Exception as e:
                logger.warning(f"  Failed to load Robinhood CSV: {e}")

        # Fall back to latest snapshot with detailed holdings
        try:
            holdings_detail_path = Path("results/monitoring/holdings_detail.csv")
            if holdings_detail_path.exists():
                holdings_detail_df = pd.read_csv(holdings_detail_path)
                if len(holdings_detail_df) > 0:
                    # Get most recent holdings
                    latest_date = holdings_detail_df['date'].max()
                    latest_holdings = holdings_detail_df[holdings_detail_df['date'] == latest_date].copy()

                    # Remove the date column
                    latest_holdings = latest_holdings.drop('date', axis=1)

                    logger.info(f"  Loaded {len(latest_holdings)} holdings from snapshot: {latest_date}")
                    return latest_holdings
        except Exception as e:
            logger.warning(f"  Failed to load holdings detail: {e}")

        # Try basic snapshot as last resort
        try:
            snapshot_path = Path("results/monitoring/portfolio_snapshots.csv")
            if snapshot_path.exists():
                snapshots_df = pd.read_csv(snapshot_path)
                if len(snapshots_df) > 0:
                    logger.warning("  No holdings detail found. Please provide Robinhood CSV or run dashboard first.")
                    return None
        except Exception as e:
            logger.warning(f"  Failed to load snapshot: {e}")

        return None

    def _get_top_movers(self, holdings_df: pd.DataFrame) -> Dict[str, List[tuple]]:
        """Get top gaining and declining stocks."""

        movers = {'up': [], 'down': []}

        if 'price_change_pct' not in holdings_df.columns:
            return movers

        # Sort by change
        holdings_sorted = holdings_df.sort_values('price_change_pct', ascending=False)

        # Top gainers
        gainers = holdings_sorted[holdings_sorted['price_change_pct'] > 0].head(5)
        movers['up'] = [
            (row['symbol'], row['price_change_pct'])
            for _, row in gainers.iterrows()
        ]

        # Top decliners
        decliners = holdings_sorted[holdings_sorted['price_change_pct'] < 0].tail(5)
        movers['down'] = [
            (row['symbol'], row['price_change_pct'])
            for _, row in decliners.iterrows()
        ]

        return movers

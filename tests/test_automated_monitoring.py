#!/usr/bin/env python3
"""
Test Automated Daily Monitoring System
"""

from loguru import logger
from src.automation import DailyMonitor

logger.info("="*80)
logger.info("TESTING AUTOMATED DAILY MONITORING")
logger.info("="*80)

# Configure email (optional - set to None for dry-run)
email_config = None  # Replace with your config to test email
# email_config = {
#     'sender_email': 'your-email@gmail.com',
#     'sender_password': 'your-app-password',  # Gmail App Password
#     'recipient_email': 'your-email@gmail.com'  # Can be same as sender
# }

# Robinhood CSV path (or None to use snapshots)
robinhood_csv = "/Users/nghiadang/Downloads/stocks_data_2025-11-10_13-50-31.csv"

# Initialize monitor
monitor = DailyMonitor(
    email_config=email_config,
    robinhood_csv_path=robinhood_csv
)

# Run daily check (dry-run mode without email)
logger.info("\nRunning daily monitoring check...")
logger.info("Email: " + ("Enabled" if email_config else "Disabled (dry-run)"))

results = monitor.run_daily_check(
    use_llm_for_news=False,  # Set to True for better sentiment analysis (slower)
    send_email=False,  # Set to True to test email
    send_critical_alerts=False  # Set to True to test critical alerts
)

logger.info("\n" + "="*80)
logger.info("TEST RESULTS:")
logger.info("="*80)

if results.get('success'):
    logger.success("✅ Daily monitoring completed successfully!")
    logger.info(f"\n  Portfolio Value: ${results['portfolio_value']:,.2f}")
    logger.info(f"  Daily Change: ${results['daily_change']:+,.2f} ({results['daily_change_pct']:+.2f}%)")
    logger.info(f"  Holdings: {results['num_holdings']}")

    alerts_summary = results.get('alerts')
    if alerts_summary is not None and len(alerts_summary) > 0:
        critical = len(alerts_summary[alerts_summary['severity'] == 'critical'])
        warnings = len(alerts_summary[alerts_summary['severity'] == 'warning'])
        logger.info(f"  Alerts: {critical} critical, {warnings} warnings")

    logger.info("\n📧 To enable email notifications:")
    logger.info("  1. Update email_config in this script")
    logger.info("  2. For Gmail: Create App Password at https://myaccount.google.com/apppasswords")
    logger.info("  3. Set send_email=True")

    logger.info("\n⏰ To schedule daily monitoring:")
    logger.info("  Run: python run_daily_monitor.py")

else:
    logger.error(f"❌ Monitoring failed: {results.get('error')}")

logger.info("="*80)

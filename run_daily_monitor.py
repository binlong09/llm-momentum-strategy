#!/usr/bin/env python3
"""
Scheduled Daily Portfolio Monitor

Runs at 4:30 PM ET daily (after market close)
"""

import schedule
import time
from datetime import datetime
from loguru import logger
from pathlib import Path
from src.automation import DailyMonitor

# ============================================================================
# CONFIGURATION - UPDATE THESE SETTINGS
# ============================================================================

# Email configuration (REQUIRED for notifications)
EMAIL_CONFIG = {
    'sender_email': 'nguthinhan10@gmail.com',  # YOUR_EMAIL@gmail.com
    'sender_password': 'qqaz geow iexj tzdh',  # YOUR_GMAIL_APP_PASSWORD
    'recipient_email': 'binlong09@gmail.com'  # Recipient email (can be same as sender)
}

# Robinhood CSV path (optional - will use latest snapshot if not provided)
ROBINHOOD_CSV_PATH = "/Users/nghiadang/Downloads/stocks_data_2025-11-10_13-50-31.csv"

# Monitoring settings
USE_LLM_FOR_NEWS = True  # True = better analysis but slower (uses OpenAI API)
SEND_EMAIL = True  # Send daily summary email
SEND_CRITICAL_ALERTS = True  # Send immediate alerts for critical events

# Schedule time (24-hour format)
SCHEDULE_TIME = "16:30"  # 4:30 PM ET

# ============================================================================


def run_monitoring():
    """Run daily monitoring task."""
    logger.info("\n" + "="*80)
    logger.info(f"SCHEDULED MONITORING - {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    logger.info("="*80)

    # Check if email is configured
    email_enabled = all([
        EMAIL_CONFIG.get('sender_email'),
        EMAIL_CONFIG.get('sender_password')
    ])

    if not email_enabled:
        logger.warning("⚠️ Email not configured! Running in DRY-RUN mode.")
        logger.warning("  Update EMAIL_CONFIG in run_daily_monitor.py")

    # Initialize monitor
    monitor = DailyMonitor(
        email_config=EMAIL_CONFIG if email_enabled else None,
        robinhood_csv_path=ROBINHOOD_CSV_PATH
    )

    # Run daily check
    results = monitor.run_daily_check(
        use_llm_for_news=USE_LLM_FOR_NEWS,
        send_email=SEND_EMAIL and email_enabled,
        send_critical_alerts=SEND_CRITICAL_ALERTS and email_enabled
    )

    if results.get('success'):
        logger.success("✅ Daily monitoring completed successfully!")
    else:
        logger.error(f"❌ Monitoring failed: {results.get('error')}")

    logger.info("="*80)
    return results


def main():
    """Main scheduler loop."""
    logger.info("="*80)
    logger.info("DAILY PORTFOLIO MONITOR - SCHEDULER")
    logger.info("="*80)
    logger.info(f"Scheduled time: {SCHEDULE_TIME} daily")
    logger.info(f"Email notifications: {'Enabled' if EMAIL_CONFIG.get('sender_email') else 'DISABLED - Update config!'}")
    logger.info(f"LLM news analysis: {'Enabled' if USE_LLM_FOR_NEWS else 'Disabled'}")
    logger.info("="*80)

    # Check configuration
    if not EMAIL_CONFIG.get('sender_email'):
        logger.warning("\n⚠️ EMAIL NOT CONFIGURED")
        logger.warning("To enable email notifications:")
        logger.warning("  1. Edit run_daily_monitor.py")
        logger.warning("  2. Update EMAIL_CONFIG with your email/password")
        logger.warning("  3. For Gmail: Create App Password at https://myaccount.google.com/apppasswords")
        logger.warning("")

    # Schedule the task
    schedule.every().day.at(SCHEDULE_TIME).do(run_monitoring)

    logger.info(f"\n⏰ Waiting for scheduled time ({SCHEDULE_TIME})...")
    logger.info("Press Ctrl+C to stop\n")

    # Run immediately on first start (optional - comment out if you don't want this)
    logger.info("🚀 Running initial check now...")
    run_monitoring()

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\n\n👋 Scheduler stopped by user")


if __name__ == "__main__":
    main()

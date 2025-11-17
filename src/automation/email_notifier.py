"""
Email Notifier - Send portfolio monitoring alerts via email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import pandas as pd


class EmailNotifier:
    """Send email notifications for portfolio monitoring."""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        recipient_email: Optional[str] = None
    ):
        """
        Initialize email notifier.

        Args:
            smtp_server: SMTP server address (default: Gmail)
            smtp_port: SMTP port (default: 587 for TLS)
            sender_email: Sender email address
            sender_password: App password for sender email
            recipient_email: Recipient email address (defaults to sender)

        Note:
            For Gmail, you need to create an App Password:
            1. Go to Google Account settings
            2. Security → 2-Step Verification (enable it)
            3. App passwords → Create new app password
            4. Use that password here (not your regular Gmail password)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email or sender_email

    def send_daily_summary(
        self,
        portfolio_value: float,
        daily_change: float,
        daily_change_pct: float,
        alerts_df: pd.DataFrame,
        news_df: pd.DataFrame,
        top_movers: Dict[str, List[tuple]]
    ) -> bool:
        """
        Send daily portfolio summary email.

        Args:
            portfolio_value: Current portfolio value
            daily_change: Dollar change today
            daily_change_pct: Percent change today
            alerts_df: Alerts DataFrame
            news_df: News monitoring DataFrame
            top_movers: Dict with 'up' and 'down' lists of (symbol, pct_change)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured. Skipping email.")
            return False

        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📊 Daily Portfolio Summary - {datetime.now().strftime('%m/%d/%Y')}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Generate email body
            html_body = self._generate_html_summary(
                portfolio_value,
                daily_change,
                daily_change_pct,
                alerts_df,
                news_df,
                top_movers
            )

            # Attach HTML
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.success(f"Daily summary email sent to {self.recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _generate_html_summary(
        self,
        portfolio_value: float,
        daily_change: float,
        daily_change_pct: float,
        alerts_df: pd.DataFrame,
        news_df: pd.DataFrame,
        top_movers: Dict[str, List[tuple]]
    ) -> str:
        """Generate HTML email body."""

        # Determine color based on change
        change_color = "#16a34a" if daily_change >= 0 else "#dc2626"
        change_sign = "+" if daily_change >= 0 else ""

        # Count alerts by severity
        critical_count = len(alerts_df[alerts_df['severity'] == 'critical']) if len(alerts_df) > 0 else 0
        warning_count = len(alerts_df[alerts_df['severity'] == 'warning']) if len(alerts_df) > 0 else 0

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .portfolio-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .daily-change {{
            font-size: 20px;
            color: {change_color};
            font-weight: 600;
        }}
        .section {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #1f2937;
            font-size: 18px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        .alert-critical {{
            background: #fee2e2;
            border-left: 4px solid #dc2626;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .alert-warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .mover {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .mover:last-child {{
            border-bottom: none;
        }}
        .positive {{ color: #16a34a; font-weight: 600; }}
        .negative {{ color: #dc2626; font-weight: 600; }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }}
        a {{
            color: #667eea;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Daily Portfolio Summary</h1>
        <div style="opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y')}</div>
        <div class="portfolio-value">${portfolio_value:,.2f}</div>
        <div class="daily-change">{change_sign}${abs(daily_change):,.2f} ({change_sign}{daily_change_pct:.2f}%)</div>
    </div>
"""

        # Alerts section
        if critical_count > 0 or warning_count > 0:
            html += """
    <div class="section">
        <h2>🚨 Alerts</h2>
"""
            # Critical alerts
            if critical_count > 0:
                critical_alerts = alerts_df[alerts_df['severity'] == 'critical']
                for _, alert in critical_alerts.iterrows():
                    html += f"""
        <div class="alert-critical">
            <strong>{alert['symbol']}</strong><br>
            {alert['message']}<br>
            <small>Action: {alert['action']}</small>
        </div>
"""

            # Warning alerts
            if warning_count > 0:
                warning_alerts = alerts_df[alerts_df['severity'] == 'warning'].head(3)  # Top 3
                for _, alert in warning_alerts.iterrows():
                    html += f"""
        <div class="alert-warning">
            <strong>{alert['symbol']}</strong><br>
            {alert['message']}<br>
            <small>Action: {alert['action']}</small>
        </div>
"""

            html += """
    </div>
"""
        else:
            html += """
    <div class="section">
        <h2>✅ No Critical Alerts</h2>
        <p style="color: #059669;">Portfolio is healthy. No immediate action required.</p>
    </div>
"""

        # Top movers section
        if top_movers and (top_movers.get('up') or top_movers.get('down')):
            html += """
    <div class="section">
        <h2>📈 Top Movers</h2>
"""
            # Top gainers
            if top_movers.get('up'):
                html += "<h3 style='font-size: 14px; color: #16a34a;'>⬆️ Top Gainers</h3>"
                for symbol, pct_change in top_movers['up'][:3]:
                    html += f"""
        <div class="mover">
            <span>{symbol}</span>
            <span class="positive">+{pct_change:.2f}%</span>
        </div>
"""

            # Top losers
            if top_movers.get('down'):
                html += "<h3 style='font-size: 14px; color: #dc2626; margin-top: 15px;'>⬇️ Top Decliners</h3>"
                for symbol, pct_change in top_movers['down'][:3]:
                    html += f"""
        <div class="mover">
            <span>{symbol}</span>
            <span class="negative">{pct_change:.2f}%</span>
        </div>
"""

            html += """
    </div>
"""

        # News summary
        if len(news_df) > 0:
            news_with_alerts = news_df[news_df['alert_level'].isin(['critical', 'warning'])]
            if len(news_with_alerts) > 0:
                html += """
    <div class="section">
        <h2>📰 News Highlights</h2>
"""
                for _, row in news_with_alerts.head(3).iterrows():
                    emoji = "🚨" if row['alert_level'] == 'critical' else "⚠️"
                    html += f"""
        <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 4px;">
            <strong>{emoji} {row['symbol']}</strong><br>
            <small>{row['summary']}</small>
        </div>
"""
                html += """
    </div>
"""

        # Footer
        html += f"""
    <div class="footer">
        <p>
            Generated by LLM Momentum Strategy System<br>
            {datetime.now().strftime('%I:%M %p ET')}<br>
            <a href="http://localhost:8501">Open Dashboard</a>
        </p>
    </div>
</body>
</html>
"""

        return html

    def send_critical_alert(
        self,
        symbol: str,
        message: str,
        action: str,
        evidence_url: Optional[str] = None
    ) -> bool:
        """
        Send immediate alert for critical event.

        Args:
            symbol: Stock symbol
            message: Alert message
            action: Recommended action
            evidence_url: URL to news article (optional)

        Returns:
            True if sent successfully
        """
        if not self.sender_email or not self.sender_password:
            return False

        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"🚨 CRITICAL ALERT: {symbol}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="background: #fee2e2; border-left: 4px solid #dc2626; padding: 20px; border-radius: 4px;">
        <h2 style="color: #dc2626; margin-top: 0;">🚨 CRITICAL ALERT</h2>
        <h3>{symbol}</h3>
        <p><strong>Alert:</strong> {message}</p>
        <p><strong>Recommended Action:</strong> {action}</p>
        {f'<p><a href="{evidence_url}">View Evidence</a></p>' if evidence_url else ''}
        <p style="font-size: 12px; color: #666; margin-top: 20px;">
            {datetime.now().strftime('%I:%M %p ET on %B %d, %Y')}
        </p>
    </div>
</body>
</html>
"""

            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            logger.success(f"Critical alert sent for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to send critical alert: {e}")
            return False

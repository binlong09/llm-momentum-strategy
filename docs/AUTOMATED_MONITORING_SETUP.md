# 🤖 Automated Daily Monitoring Setup Guide

**Never miss a critical portfolio event again!**

---

## What You Just Built

A fully automated daily monitoring system that:
- ✅ Checks your portfolio every day at 4:30 PM ET (after market close)
- ✅ Scans news for all holdings with evidence URLs
- ✅ Generates alerts based on severity (Critical/Warning/Info)
- ✅ Sends email summaries with portfolio performance
- ✅ Immediately alerts you to critical events (fraud, bankruptcy, etc.)
- ✅ Includes analyst ratings in LLM sentiment analysis (Phase 3 complete!)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Required Package
```bash
pip install schedule
```

### Step 2: Configure Email (Gmail)

1. **Enable 2-Step Verification**:
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification" (required for app passwords)

2. **Create App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Mac" (or your device)
   - Click "Generate"
   - Copy the 16-character password (like: `abcd efgh ijkl mnop`)

3. **Update Configuration**:
   Edit `run_daily_monitor.py`:
   ```python
   EMAIL_CONFIG = {
       'sender_email': 'your-email@gmail.com',
       'sender_password': 'abcd efgh ijkl mnop',  # App password from step 2
       'recipient_email': 'your-email@gmail.com'   # Can be same as sender
   }
   ```

### Step 3: Test the System
```bash
python test_automated_monitoring.py
```

You should see:
```
✅ Daily monitoring completed successfully!
  Portfolio Value: $XX,XXX.XX
  Daily Change: $+XX.XX (+0.XX%)
  Holdings: 25
  Alerts: 0 critical, 1 warnings
```

### Step 4: Run Scheduled Monitoring
```bash
python run_daily_monitor.py
```

This will:
- Run immediately once (test)
- Then wait until 4:30 PM ET daily
- Run automatically every day at that time
- Send you email summary after each run

---

## 📧 Email Notifications

### Daily Summary Email (4:30 PM ET)

You'll receive a beautiful HTML email with:

**Header:**
- Portfolio value
- Daily change ($ and %)
- Color-coded performance

**Alerts Section:**
- 🚨 Critical alerts (if any) with evidence
- ⚠️ Warning alerts (top 3)
- ✅ "No critical alerts" if portfolio healthy

**Top Movers:**
- ⬆️ Top 3 gainers with % change
- ⬇️ Top 3 decliners with % change

**News Highlights:**
- Summary of critical/warning news
- Direct links to articles

**Footer:**
- Timestamp
- Link to open dashboard

### Critical Alert Emails (Immediate)

For critical events (fraud, bankruptcy, SEC investigation), you'll get:
- 🚨 Subject: "CRITICAL ALERT: [SYMBOL]"
- Immediate notification (not waiting for daily summary)
- Evidence URL to news article
- Recommended action

---

## ⚙️ Configuration Options

Edit `run_daily_monitor.py` to customize:

```python
# Email configuration
EMAIL_CONFIG = {
    'sender_email': 'your-email@gmail.com',
    'sender_password': 'your-app-password',
    'recipient_email': 'alerts@example.com'  # Can be different
}

# Robinhood CSV path (optional - uses snapshots if not provided)
ROBINHOOD_CSV_PATH = "/path/to/robinhood_export.csv"

# LLM for news analysis (includes analyst ratings - Phase 3!)
USE_LLM_FOR_NEWS = False  # True = better but slower + costs OpenAI credits

# Email settings
SEND_EMAIL = True  # Daily summary
SEND_CRITICAL_ALERTS = True  # Immediate critical alerts

# Schedule time (24-hour format, Eastern Time)
SCHEDULE_TIME = "16:30"  # 4:30 PM ET (after market close)
```

---

## 🔄 Running Options

### Option A: Manual Run (Test)
```bash
python test_automated_monitoring.py
```
- Runs once immediately
- No email sent (dry-run mode)
- Good for testing

### Option B: Scheduled Run (Foreground)
```bash
python run_daily_monitor.py
```
- Runs immediately once
- Then waits for scheduled time
- Runs daily at 4:30 PM ET
- Keeps terminal open
- Press Ctrl+C to stop

### Option C: Background Run (macOS/Linux)
```bash
nohup python run_daily_monitor.py > monitor.log 2>&1 &
```
- Runs in background
- Survives terminal closing
- Logs to `monitor.log`
- To stop: `ps aux | grep run_daily_monitor` then `kill [PID]`

### Option D: System Service (Always Running)

**macOS (launchd):**
Create `~/Library/LaunchAgents/com.momentum.monitor.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.momentum.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/run_daily_monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.momentum.monitor.plist
```

**Linux (systemd):**
Create `/etc/systemd/system/momentum-monitor.service`:
```ini
[Unit]
Description=Momentum Portfolio Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python /path/to/run_daily_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable momentum-monitor
sudo systemctl start momentum-monitor
```

---

## 🧪 What Gets Monitored

### 1. Portfolio Performance
- Current value
- Daily change ($ and %)
- Comparison to previous day
- Top gainers/decliners

### 2. News Monitoring
- **Phase 3 Enhancement:** Now includes analyst ratings!
- Scans 5 news sources (Yahoo, CNBC, MarketWatch, WSJ, Seeking Alpha)
- Context-aware keyword detection (reduced false positives)
- Evidence collection with URLs
- LLM sentiment analysis (optional, with analyst data)

### 3. Alert Generation
- **Critical:** 2+ high-relevance red flags, >15% price drop
- **Warning:** 1 red flag, 10-15% drop, 3+ warnings
- **Info:** Normal volatility, positive news, take-profit opportunities

### 4. Analyst Ratings (NEW - Phase 3!)
When `USE_LLM_FOR_NEWS = True`, the LLM now considers:
- Buy/Hold/Sell recommendations
- Price targets and upside potential
- Earnings growth estimates
- Recent upgrades/downgrades

This helps distinguish real concerns from noise. Example:
- Stock drops 12% + analyst downgrade = Real concern
- Stock drops 12% + analyst upgrade = Buying opportunity

---

## 📊 Example Email

```
📊 Daily Portfolio Summary
Sunday, November 10, 2025

$10,075.57
+$23.45 (+0.23%)

✅ No Critical Alerts
Portfolio is healthy. No immediate action required.

📈 Top Movers

⬆️ Top Gainers
NVDA      +3.24%
AAPL      +2.15%
MSFT      +1.89%

⬇️ Top Decliners
TSLA      -2.45%
META      -1.67%
GOOGL     -0.98%

Generated by LLM Momentum Strategy System
04:30 PM ET
Open Dashboard
```

---

## 🛠️ Troubleshooting

### Email Not Sending

**Problem:** "Failed to send email"

**Solutions:**
1. Check Gmail App Password (not regular password)
2. Verify 2-Step Verification is enabled
3. Try with `sender_email == recipient_email` first
4. Check firewall/antivirus isn't blocking port 587
5. Test with: `python test_automated_monitoring.py` (set `send_email=True`)

### No Portfolio Data

**Problem:** "No portfolio data available"

**Solutions:**
1. Export latest CSV from Robinhood
2. Update `ROBINHOOD_CSV_PATH` in config
3. Or run monitoring from dashboard first to create snapshot

### Scheduler Not Running

**Problem:** Script exits immediately

**Solutions:**
1. Check schedule time format: "16:30" (24-hour)
2. Ensure `schedule` package installed: `pip install schedule`
3. Check logs for errors
4. Run in foreground first to debug

### LLM Errors (Phase 3)

**Problem:** "LLM sentiment failed"

**Solutions:**
1. Check OpenAI API key in `.env`
2. Verify API credits available
3. Set `USE_LLM_FOR_NEWS = False` if not needed (faster, free)
4. LLM is optional - keyword detection still works without it

---

## 💡 Best Practices

### 1. Keep Email Concise
- Only critical/warning alerts in email
- Full details available in dashboard
- Reduces email fatigue

### 2. Test Before Relying
- Run `test_automated_monitoring.py` first
- Verify email arrives correctly
- Check portfolio value is accurate

### 3. Monitor the Monitor
- Check logs occasionally
- Verify emails still arriving
- Test after system updates

### 4. Security
- Don't commit email credentials to git
- Use environment variables if possible
- Rotate app passwords periodically

### 5. Customize for Your Workflow
- Adjust `SCHEDULE_TIME` to your preference
- Enable/disable LLM based on needs
- Modify alert thresholds in code if needed

---

## 🎯 Next Steps

1. **Today:** Set up email and test
2. **This Week:** Run scheduled monitoring daily
3. **Next Week:** Review alert accuracy, adjust if needed
4. **Month 1:** Evaluate if LLM adds value (Phase 3 feature)
5. **Optional:** Set up as system service for always-on monitoring

---

## 📈 Performance Impact

**Without LLM (`USE_LLM_FOR_NEWS = False`):**
- Runtime: ~20 seconds for 25 stocks
- Cost: $0 (uses free RSS feeds)
- Accuracy: Good (keyword detection + context)

**With LLM + Analyst Ratings (`USE_LLM_FOR_NEWS = True`):**
- Runtime: ~60 seconds for 25 stocks
- Cost: ~$0.10 per run (OpenAI gpt-4o-mini)
- Accuracy: Better (understands nuance + analyst context)
- **NEW:** Now includes analyst ratings from Phase 3!

**Recommendation:** Start without LLM, enable if false positives occur.

---

## 🎉 Congratulations!

You now have a fully automated portfolio monitoring system that:
- Watches your portfolio 24/7
- Alerts you to critical events immediately
- Sends daily summaries with performance
- Uses analyst ratings for better sentiment (Phase 3!)
- Provides evidence URLs for every alert
- Reduces false positives with context-aware detection

**Never miss a critical portfolio event again!** 🚀

---

## 📞 Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review logs in terminal/monitor.log
3. Test individual components:
   - News monitor: `python test_phase3_integration.py`
   - Full system: `python test_automated_monitoring.py`

---

*Last updated: November 10, 2025*
*Phase 3 (Analyst Ratings) integration complete!*

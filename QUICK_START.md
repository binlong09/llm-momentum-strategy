# 🚀 Quick Start: Automated Monitoring

## ⚡ 5-Minute Setup

### 1. Install Package
```bash
pip install schedule
```

### 2. Configure Email
Edit `run_daily_monitor.py`:
```python
EMAIL_CONFIG = {
    'sender_email': 'your@gmail.com',
    'sender_password': 'your-16-char-app-password',  # Not regular password!
    'recipient_email': 'your@gmail.com'
}
```

**Get Gmail App Password:** https://myaccount.google.com/apppasswords

### 3. Test
```bash
python test_automated_monitoring.py
```

### 4. Run
```bash
python run_daily_monitor.py
```

---

## 📧 What You'll Get

**Every day at 4:30 PM ET:**
- Email with portfolio value & daily change
- Critical alerts (if any) with evidence URLs
- Top 3 gainers and decliners
- News highlights

**Immediately for critical events:**
- Fraud, bankruptcy, SEC investigation
- Separate urgent email with evidence

---

## 🎯 What It Does

1. **4:30 PM ET:** Runs automatically
2. **Updates prices** from Yahoo Finance
3. **Scans news** from 5 sources
4. **Uses analyst ratings** for better sentiment (Phase 3!)
5. **Generates alerts** (Critical/Warning/Info)
6. **Sends email** with beautiful HTML summary

---

## ⚙️ Options

**Without LLM** (Default):
- Fast (~20 seconds)
- Free
- Good accuracy

**With LLM** (Optional):
- Slower (~60 seconds)
- ~$0.10/day OpenAI cost
- Better accuracy + analyst ratings

Enable in `run_daily_monitor.py`:
```python
USE_LLM_FOR_NEWS = True
```

---

## 📚 Full Documentation

- **Setup Guide:** `AUTOMATED_MONITORING_SETUP.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **Alert Guide:** `ALERT_INTERPRETATION_GUIDE.md`
- **User Guide:** `HOW_TO_USE_MONITORING.md`

---

## 🆘 Troubleshooting

**Email not sending?**
- Use Gmail App Password (not regular password)
- Enable 2-Step Verification first
- Check firewall isn't blocking port 587

**No portfolio data?**
- Export Robinhood CSV
- Update `ROBINHOOD_CSV_PATH`
- Or run dashboard first to create snapshot

**Scheduler not working?**
- Check time format: "16:30" (24-hour)
- Ensure `schedule` installed
- Run in foreground first to debug

---

## ✅ Success Checklist

- [ ] Gmail App Password created
- [ ] Config updated in `run_daily_monitor.py`
- [ ] Test passed: `python test_automated_monitoring.py`
- [ ] Scheduler started: `python run_daily_monitor.py`
- [ ] First email received at 4:30 PM ET
- [ ] Verified alerts are accurate

---

**That's it! Your portfolio is now monitored 24/7!** 🎉

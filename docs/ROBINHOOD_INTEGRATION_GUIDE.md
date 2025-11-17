# 🎯 Robinhood API Integration Guide

## Overview

The dashboard now **automatically fetches your current portfolio from Robinhood** and shows you exactly what to trade. This eliminates manual CSV tracking while keeping you in full control (no trades are executed automatically).

---

## ✅ What This Does

**✅ Automatically fetches:**
- Current positions
- Portfolio value
- Share counts and prices
- Current weights

**✅ Shows you:**
- What to sell (positions dropping out)
- What to buy (new positions)
- What to rebalance (with exact dollar amounts)
- Live comparison (current vs target)

**❌ Does NOT:**
- Execute any trades
- Require you to trust the app with trading permissions
- Save your password (connection is temporary)

---

## 🚀 Quick Start

### Month 1 (Initial Investment)

1. **Generate Portfolio**
   - Go to "Generate Portfolio" tab
   - Generate 20-stock portfolio

2. **Go to Robinhood Orders tab**
   - Capital: Enter $10,000 (or your amount)
   - Skip "Connect to Robinhood" (no holdings yet)
   - Click "Generate Order List"

3. **Execute on Robinhood**
   - Download CSV
   - Execute all 20 BUY orders

### Month 2+ (With Robinhood Integration)

1. **Generate New Portfolio**
   - Go to "Generate Portfolio" tab
   - Generate fresh portfolio with latest data

2. **Go to Robinhood Orders tab**
   - Choose: "🔗 Connect to Robinhood API (Automatic)"
   - Enter credentials + 2FA code
   - Click "Fetch Current Holdings"
   - Capital auto-fills!

3. **See What Changed**
   - Click "Generate Order List"
   - See only 2-4 trades needed (instead of 20!)
   - Exact current vs target comparison

4. **Execute**
   - Follow step-by-step instructions
   - Much faster than Month 1!

---

## 🔐 Security & Privacy

### How Login Works

**What happens:**
1. You enter credentials in the dashboard
2. `robin_stocks` library connects to Robinhood's unofficial API
3. Session is established (read-only)
4. Credentials are NOT saved anywhere
5. When you close the dashboard, session ends

**2FA Support:**
- If 2FA is enabled, you'll need the 6-digit code
- Get it from your authenticator app (Google Authenticator, Authy, etc.)
- After first successful login, a device token is saved locally
- Future logins won't require 2FA (like Robinhood app)

### What Gets Accessed

**Read permissions only:**
- ✅ Account equity (total value)
- ✅ Current positions (symbols, shares, prices)
- ✅ Cost basis and P&L

**NOT accessed:**
- ❌ Cannot place orders
- ❌ Cannot transfer funds
- ❌ Cannot change account settings
- ❌ No access to personal info beyond holdings

### Credentials Storage

**Important:**
- Credentials are entered in-session only
- NOT saved to disk
- NOT logged anywhere
- Connection is temporary (ends when you close dashboard)

**Device token:**
- Saved locally as `.robinhood_device_token`
- Allows skipping 2FA on future logins
- Can be deleted anytime to revoke

---

## 📋 Step-by-Step: Month 2 Workflow

### 1. Launch Dashboard

```bash
cd /Users/nghiadang/AIProjects/llm_momentum_strategy
source venv/bin/activate
streamlit run dashboard.py
```

Open: http://localhost:8501

---

### 2. Generate New Portfolio

**Go to "💼 Generate Portfolio" tab:**
- Portfolio size: 20
- Enable LLM enhancement
- Select model (default: gpt-4o-mini)
- Click "Generate Portfolio"

Wait for completion (1-2 minutes).

---

### 3. Connect to Robinhood

**Go to "🎯 Robinhood Orders" tab:**

**Portfolio:**
- ✅ Should auto-detect from previous step

**Capital:**
- Will auto-fill after connecting to Robinhood

**Get Current Holdings:**
1. Choose: "🔗 Connect to Robinhood API (Automatic)"
2. Enter your Robinhood email/username
3. Enter your Robinhood password
4. Enter 2FA code (if enabled)
5. Click "🔐 Connect to Robinhood"

**Wait for:** "✅ Connected to Robinhood as [your_email]"

---

### 4. Fetch Live Holdings

1. Click "📥 Fetch Current Holdings"
2. Wait 5-10 seconds
3. See: "✅ Fetched 20 positions ($10,847.32 total)"
4. Notice capital auto-filled to $10,847.32!

**Optional:** Click "👀 View Current Holdings" to see your positions.

---

### 5. Generate Rebalancing Orders

**Click: "🎯 Generate Robinhood Order List"**

**What you'll see:**

```
📋 STEP-BY-STEP ROBINHOOD ORDERS

Metrics:
Total Positions: 20  |  Sells: 2  |  Buys: 2  |  Turnover: 20.0%

────────────────────────────────────────
STEP 1: SELL ORDERS (Exit Positions)
Sell these 2 positions completely

| Step | Action | Symbol | Amount | Instructions            |
|------|--------|--------|--------|-------------------------|
| 1.1  | SELL   | EBAY   | ALL    | Sell 100% of position   |
| 1.2  | SELL   | FOX    | ALL    | Sell 100% of position   |

────────────────────────────────────────
STEP 2: BUY NEW POSITIONS
Buy these 2 new stocks

| Step | Action | Symbol | Amount    | Weight | Instructions                      |
|------|--------|--------|-----------|--------|-----------------------------------|
| 2.1  | BUY    | NVDA   | $650.56   | 6.01%  | Buy $650.56 worth (use "Dollars") |
| 2.2  | BUY    | PLTR   | $650.56   | 6.01%  | Buy $650.56 worth (use "Dollars") |

────────────────────────────────────────
STEP 3: REBALANCE EXISTING POSITIONS (Optional)
Adjust these 16 positions if weights drifted significantly (>2%)

| Step | Symbol | Target Value | Target Weight | Current Value | Current Weight | Difference | Action              |
|------|--------|--------------|---------------|---------------|----------------|------------|---------------------|
| 3.1  | APP    | $650.56      | 6.01%         | $730.22       | 6.73%          | -$79.66    | SELL $79.66         |
| 3.2  | GOOGL  | $650.56      | 6.01%         | $645.11       | 5.95%          | +$5.45     | HOLD (close enough) |
| 3.3  | IBKR   | $650.56      | 6.01%         | $598.33       | 5.52%          | +$52.23    | BUY $52.23          |
...

✨ Live data from Robinhood: Showing exact current vs target values!
```

**Notice:**
- ✨ Current values are shown (not just targets!)
- ✨ Exact difference calculated for you
- ✨ "HOLD (close enough)" for positions within 2%

---

### 6. Download & Execute

**Download Order List:**
- Click "📥 Download Order List (CSV)"
- Save to desktop or print

**Execute on Robinhood:**
- Open Robinhood app/website
- Follow STEP 1: Sell 2 positions
- Follow STEP 2: Buy 2 positions
- Optional: Follow STEP 3 for major rebalancing (>$50 or >2%)

**Time: 10-15 minutes** (vs 40 minutes without API integration!)

---

### 7. Disconnect (Optional)

**After you're done:**
- Click "🚪 Disconnect" to logout
- Closes session
- Next month you can reconnect (no 2FA needed if device token exists)

---

## 🆚 Comparison: Manual vs API

### Without Robinhood API (Old Way)

**Month 2 workflow:**
1. Generate new portfolio (2 min)
2. **Manually export holdings from Robinhood** (5 min)
3. **Manually create CSV** (5 min)
4. Upload CSV to dashboard (1 min)
5. **Manually enter capital** (1 min)
6. Generate order list (1 min)
7. **Manually calculate rebalancing amounts** (10 min)
8. Execute trades (20 min)

**Total: ~45 minutes**

### With Robinhood API (New Way)

**Month 2 workflow:**
1. Generate new portfolio (2 min)
2. **Click "Connect to Robinhood"** (30 sec)
3. **Click "Fetch Holdings"** (10 sec)
4. Capital auto-fills automatically
5. Generate order list (1 min)
6. Rebalancing amounts calculated automatically
7. Execute trades (10 min)

**Total: ~15 minutes**

**Time saved: 30 minutes/month = 6 hours/year!**

---

## 🔧 Troubleshooting

### Login Fails

**Error: "Login failed. Check credentials."**
- Double-check username and password
- Make sure Robinhood account is active
- Try resetting password on Robinhood app

**Error: "2FA code required."**
- Enter 6-digit code from authenticator app
- Code must be current (refreshes every 30 seconds)
- If still failing, try next code

### Can't Fetch Holdings

**Error: "Not logged in. Call login() first."**
- Connection was lost
- Click "Disconnect" then reconnect

**Error: "Error fetching positions: [API error]"**
- Robinhood API may be temporarily down
- Wait 5 minutes and try again
- Fallback: Use manual CSV upload instead

### 2FA Issues

**"I don't have 2FA enabled"**
- Leave the 2FA field blank
- Just enter username and password

**"I can't find my 2FA code"**
- Check your authenticator app (Google Authenticator, Authy, etc.)
- Code is 6 digits, refreshes every 30 seconds
- If lost access, disable 2FA on Robinhood website first

### Device Token Issues

**"It keeps asking for 2FA every time"**
- Device token may not be saving
- Check file exists: `.robinhood_device_token`
- If missing, check file permissions

**"I want to revoke device token"**
```bash
rm .robinhood_device_token
```

---

## ⚠️ Important Notes

### Unofficial API

**This uses Robinhood's unofficial API:**
- Robinhood does not officially support retail API access
- The `robin_stocks` library reverse-engineers their mobile app API
- It could break if Robinhood updates their API
- Use at your own risk

**If it breaks:**
- Fallback to manual CSV upload (still works!)
- Wait for `robin_stocks` library update
- Check GitHub issues: https://github.com/jmfernandes/robin_stocks

### Rate Limits

**Robinhood may throttle requests:**
- Don't fetch holdings repeatedly
- Fetch once per session
- If you hit rate limits, wait 15 minutes

### Account Security

**Best practices:**
- Use strong, unique password
- Enable 2FA on Robinhood account
- Don't share device token file
- Logout after each session
- Don't run dashboard on public computers

---

## 🎓 Advanced Tips

### Running on Remote Server

**If running dashboard on a server:**
- Use SSH tunnel for secure access
- Never expose port 8501 publicly
- Use VPN or SSH port forwarding

**Example:**
```bash
# On server
streamlit run dashboard.py --server.port 8501

# On local machine
ssh -L 8501:localhost:8501 user@server
# Then access: http://localhost:8501
```

### Automated Device Token

**To avoid 2FA every time:**
1. Login once with 2FA
2. Device token is auto-saved
3. Future logins: just username + password
4. Token stored in `.robinhood_device_token`

**Token is valid for ~90 days.**

### Handling Multiple Accounts

**If you have multiple Robinhood accounts:**
- Each account needs separate login
- Device tokens are per-account
- Manually rename token files:
  - `.robinhood_device_token_account1`
  - `.robinhood_device_token_account2`

---

## 📊 What Data Is Shown

### Portfolio Summary

**Fetched from Robinhood:**
- Total account equity
- Number of positions
- Cash balance (if any)

### Position Details

**For each holding:**
- Symbol
- Number of shares (including fractional)
- Average cost basis
- Current price
- Market value
- Weight (% of portfolio)
- Unrealized P&L ($)
- Unrealized P&L (%)

### Comparison View

**When comparing with target:**
- Current value vs target value
- Current weight vs target weight
- Difference ($ and %)
- Recommended action (BUY/SELL/HOLD)

---

## 🆘 FAQ

### Q: Is my password saved?

**A:** No. Credentials are entered in-session only and discarded when you close the dashboard.

### Q: Can the script place trades?

**A:** No. Read-only access. You must manually execute all trades.

### Q: What if Robinhood API is down?

**A:** Fallback to manual CSV upload method (still available in the UI).

### Q: Do I need to reconnect every month?

**A:** Only if you close the dashboard or disconnect. If you keep the browser tab open, you stay connected.

### Q: Can I use this with Robinhood Gold?

**A:** Yes, works with all Robinhood account types.

### Q: What about margin accounts?

**A:** Works, but be aware of margin considerations. The script doesn't account for margin requirements.

### Q: Is this legal?

**A:** Yes. You're accessing your own account data through an unofficial but publicly available API. Not violating Robinhood TOS as long as you're not scraping data at scale or for commercial purposes.

---

## ✅ Summary

**Benefits:**
- ✨ Saves 30 min/month (6 hours/year)
- ✨ Eliminates manual CSV tracking
- ✨ Shows exact rebalancing amounts
- ✨ Auto-fills portfolio value
- ✨ Live current vs target comparison
- ✨ Still maintains full manual control

**Tradeoffs:**
- ⚠️ Unofficial API (could break)
- ⚠️ Requires entering credentials
- ⚠️ Need 2FA code on first login

**Recommendation:**
- ✅ **Use it!** Massive time savings
- ✅ Enable 2FA for security
- ✅ Keep manual CSV method as backup

---

## 🚀 Ready to Try?

**Right now:**
1. Dashboard is running at http://localhost:8501
2. Go to "🎯 Robinhood Orders" tab
3. Choose "🔗 Connect to Robinhood API"
4. Enter your credentials
5. See the magic! ✨

**Questions?** Open an issue or check the troubleshooting section above.

---

*Last updated: November 5, 2025*

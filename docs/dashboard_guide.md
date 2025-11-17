# Dashboard User Guide

## Quick Start

### Launch the Dashboard

```bash
# Activate virtual environment
source venv/bin/activate

# Launch dashboard (opens in browser automatically)
streamlit run dashboard.py
```

The dashboard will open in your default browser at `http://localhost:8501`

---

## Dashboard Features

### 🏠 Overview Tab

**What you'll see:**
- Key results summary (validation & test periods)
- Performance comparison table
- How the strategy works
- Quick start instructions

**Use this when:**
- First time using the dashboard
- Want to see overall performance at a glance
- Need to explain the strategy to others

---

### 💼 Generate Portfolio Tab

**What you'll see:**
- Interactive parameter configuration
- Portfolio generation with live LLM scoring
- Top 20 holdings display
- Position sizing calculator
- Download CSV functionality

**How to use:**

1. **Configure Parameters:**
   - Portfolio Size: 20-100 stocks (default: 50)
   - Base Weighting: equal, momentum, or inverse_vol
   - Use LLM Enhancement: Toggle GPT-4o-mini scoring
   - LLM Tilting Factor: 1.0-10.0 (default: 5.0)

2. **Click "Generate Portfolio"**
   - Wait 1-2 minutes for LLM scoring
   - Progress spinner will show while processing

3. **Review Results:**
   - Top 20 holdings table
   - Portfolio summary (total positions, max/min weights)
   - Average LLM score

4. **Calculate Position Sizes:**
   - Enter your portfolio capital
   - See dollar amount for each position
   - Use for actual trade execution

5. **Download CSV:**
   - Click "Download Portfolio CSV"
   - Save for your records
   - Use for next month's comparison

**Use this when:**
- First trading day of each month
- Want to customize portfolio parameters
- Need position sizing for trade execution

---

### 📈 Backtest Results Tab

**What you'll see:**
- Validation period metrics (2019-2023)
- Test period metrics (2024)
- Baseline vs Enhanced comparison
- Additional metrics table

**Metrics displayed:**
- Annual Return
- Sharpe Ratio
- Max Drawdown
- Sortino Ratio
- Calmar Ratio
- Volatility
- Total Return

**Use this when:**
- Reviewing historical performance
- Checking risk-adjusted returns
- Validating strategy effectiveness

---

### 📉 Performance Charts Tab

**What you'll see:**
- Interactive Plotly charts (zoom, pan, hover)
- Validation equity curve
- Test equity curve
- Drawdown analysis
- Annual returns comparison
- Static PNG charts (if available)

**Chart features:**
- Hover for exact values
- Zoom in/out with mouse
- Pan left/right
- Download as PNG
- Compare baseline vs enhanced

**Use this when:**
- Analyzing drawdown periods
- Visualizing performance trends
- Creating presentations/reports

---

### 📚 Trading Guide Tab

**What you'll see:**
- Quick monthly workflow (15 min)
- Detailed step-by-step instructions
- Expected performance metrics
- Important warnings
- Troubleshooting tips

**Sections:**
- Quick Workflow
- Detailed Steps (expandable)
  - Portfolio Generation
  - Position Sizing
  - Trade Execution
  - Performance Tracking
- Expected Performance
- Important Warnings
- Troubleshooting

**Use this when:**
- First time live trading
- Need monthly workflow reminder
- Troubleshooting issues

---

## Dashboard Tips

### Navigation

- **Sidebar**: Use radio buttons to switch between tabs
- **Quick Stats**: Always visible in sidebar (latest backtest results)
- **Wide Layout**: Dashboard uses full browser width for better data display

### Performance

- **First load**: May take 10-20 seconds to load all data
- **Portfolio generation**: Takes 1-2 minutes with LLM (50 stocks)
- **Charts**: Interactive charts load faster than static ones

### Data Sources

- **Backtest results**: Loads from `results/backtests/` (latest run)
- **Visualizations**: Loads from `results/visualizations/`
- **Portfolio generation**: Uses live data from yfinance + LLM

### Browser Compatibility

**Best experience:**
- Chrome/Edge (recommended)
- Firefox
- Safari

**Not recommended:**
- Internet Explorer

---

## Common Workflows

### Monthly Rebalancing (Recommended)

1. **Launch dashboard** on first trading day
2. Go to **"Generate Portfolio"** tab
3. Keep default settings (50 stocks, equal weighting, LLM on, η=5.0)
4. Click **"Generate Portfolio"**
5. Review top holdings
6. Enter your capital in position sizing calculator
7. Download CSV
8. Execute trades during market hours
9. Done until next month!

### Analyzing Past Performance

1. **Launch dashboard**
2. Go to **"Backtest Results"** tab
3. Review validation & test metrics
4. Go to **"Performance Charts"** tab
5. Analyze equity curves and drawdowns
6. Check if results align with expectations

### Testing Different Parameters

1. Go to **"Generate Portfolio"** tab
2. Try different settings:
   - Portfolio size: 30 vs 50 vs 75
   - Tilting factor: 2.0 vs 5.0 vs 10.0
   - Baseline only: Turn off LLM
3. Compare top holdings
4. See how weights change
5. Decide which parameters work best for you

### Creating Reports

1. Go to **"Overview"** tab → Screenshot key results
2. Go to **"Backtest Results"** → Screenshot metrics tables
3. Go to **"Performance Charts"** → Download charts as PNG
4. Combine into presentation/report

---

## Keyboard Shortcuts

**Streamlit shortcuts:**
- `R` - Rerun the dashboard
- `C` - Clear cache
- `?` - Show keyboard shortcuts

**Browser shortcuts:**
- `Cmd/Ctrl + T` - New tab (keep dashboard running)
- `Cmd/Ctrl + W` - Close tab
- `Cmd/Ctrl + Shift + T` - Reopen closed tab

---

## Troubleshooting

### Dashboard won't start

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Fix**:
```bash
source venv/bin/activate
pip install streamlit plotly
streamlit run dashboard.py
```

### No backtest results showing

**Cause**: No backtest data in `results/backtests/`

**Fix**:
```bash
python scripts/run_full_backtest.py
# Wait for completion (~5-10 minutes)
# Refresh dashboard (press R)
```

### Portfolio generation failing

**Error**: `OpenAI API error`

**Fix**:
```bash
export OPENAI_API_KEY='your-key-here'
# Restart dashboard
```

### Charts not displaying

**Cause**: Missing visualization files

**Fix**:
```bash
python scripts/create_charts.py
# Refresh dashboard (press R)
```

### Dashboard is slow

**Possible causes:**
- First time loading large datasets
- Internet connection slow (for yfinance data)
- LLM API calls taking longer

**Fixes:**
- Wait a bit longer (first load is slower)
- Check internet connection
- Use cached data (disable LLM if just testing)

---

## Advanced Usage

### Running on Different Port

```bash
streamlit run dashboard.py --server.port 8502
```

### Accessing from Another Device

```bash
# Find your local IP address
ifconfig | grep "inet "

# Run dashboard with network access
streamlit run dashboard.py --server.address 0.0.0.0

# Access from another device at http://YOUR_IP:8501
```

### Customizing Dashboard

Edit `dashboard.py` to customize:
- **Colors**: Change hex codes in Plotly charts
- **Layout**: Modify `st.columns()` ratios
- **Metrics**: Add/remove metrics in results tabs
- **Charts**: Add new chart types

**Example**: Change chart colors
```python
# In dashboard.py, find:
line=dict(color='#2E86AB', width=2.5)

# Change to your preferred color:
line=dict(color='#FF5733', width=2.5)
```

---

## FAQ

### Q: Can I run this on a server?

**A**: Yes! Use:
```bash
streamlit run dashboard.py --server.headless true --server.port 8501
```

### Q: Does the dashboard work offline?

**A**: Partially. You can view backtest results offline, but portfolio generation requires:
- Internet connection (yfinance data)
- OpenAI API access (LLM scoring)

### Q: Can I share the dashboard with others?

**A**: Yes, but:
- They need access to your machine/network
- Or deploy to Streamlit Cloud (free tier available)
- Careful with API keys (use environment variables)

### Q: How do I stop the dashboard?

**A**: Press `Ctrl+C` in the terminal where it's running

---

## Performance Optimization

### Speed up portfolio generation:

1. **Use baseline only** (no LLM):
   - Uncheck "Use LLM Enhancement"
   - Generates instantly

2. **Reduce portfolio size**:
   - 30 stocks = faster than 50 stocks
   - Fewer LLM API calls

3. **Cache data**:
   - yfinance data is cached automatically
   - Re-running same parameters is faster

---

## Best Practices

1. **Monthly routine**:
   - Set calendar reminder for first trading day
   - Launch dashboard in morning
   - Generate portfolio before market open
   - Execute during liquid hours (10 AM - 3 PM ET)

2. **Keep it running**:
   - Don't close browser tab during generation
   - Dashboard will show progress

3. **Save your work**:
   - Always download portfolio CSV
   - Keep for next month's comparison
   - Track performance in spreadsheet

4. **Review before trading**:
   - Check top holdings make sense
   - Verify LLM scores are reasonable
   - Look for data quality issues

---

## Getting Help

**Documentation**:
- This guide: `docs/dashboard_guide.md`
- Trading workflow: `docs/trading_workflow.md`
- Technical details: `docs/llm_enhanced_strategy.md`

**Code**:
- Dashboard source: `dashboard.py`
- Portfolio generation: `scripts/generate_portfolio.py`

**Issues**:
- Check existing backtest results exist
- Verify OpenAI API key is set
- Ensure virtual environment is activated

---

## Summary

The dashboard provides an **interactive, user-friendly interface** for:
- ✅ Generating monthly portfolios (with live LLM scoring)
- ✅ Analyzing backtest results (validation & test periods)
- ✅ Visualizing performance (interactive charts)
- ✅ Learning the trading workflow (step-by-step guide)

**Launch it with:**
```bash
streamlit run dashboard.py
```

**And you're ready to trade!** 🚀

---

*Last updated: November 5, 2024*

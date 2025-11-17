# 📊 LLM-Enhanced Portfolio Monitor

**Real-time portfolio monitoring dashboard with intelligent news analysis**

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🎯 What This Does

Interactive Streamlit dashboard for monitoring your stock portfolio with:

- **📈 Live portfolio tracking** - Real-time prices, daily changes, holdings overview
- **📰 Intelligent news monitoring** - AI-powered sentiment analysis with GPT-4
- **🚨 Smart alerts** - Critical event detection (fraud, bankruptcy, SEC investigations)
- **💼 Monthly rebalancing** - LLM-enhanced momentum strategy portfolio generation
- **🔍 Individual stock analysis** - Deep dive into any stock with news & analyst data
- **🎯 Robinhood integration** - Import holdings and generate trade instructions

---

## 🚀 Quick Start

### 1. Install

```bash
git clone https://github.com/YOUR_USERNAME/llm_momentum_strategy.git
cd llm_momentum_strategy
pip install -r requirements.txt
```

### 2. Configure

Set your OpenAI API key:
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

### 3. Run

```bash
streamlit run dashboard.py
```

Dashboard opens at `http://localhost:8501`

---

## 📱 Dashboard Features

### 🏠 Overview
- Current portfolio value & daily change
- Complete list of holdings with prices, weights, and performance
- Quick action links to other features

### 📊 Daily Monitor
- Upload Robinhood CSV or use latest snapshot
- Real-time price updates
- News scanning from 5 sources
- Automated alert generation
- Performance tracking over time

### 💼 Generate Portfolio
- LLM-enhanced momentum strategy
- Create monthly portfolios (25-50 stocks)
- Compare with current holdings
- View LLM scores and tilted weights

### 🔄 Monthly Rebalancing
- Compare current vs. new portfolio
- Calculate exact trades needed (buy/sell/hold)
- See expected turnover and transaction costs
- Export trade instructions

### 🔍 Analyze Individual Stock
- Comprehensive stock analysis
- Recent news with LLM sentiment
- Analyst ratings and price targets
- Earnings data and growth estimates
- Risk assessment

### 🎯 Robinhood Orders
- Generate Robinhood-specific trade instructions
- Fractional share calculations
- Order templates ready to copy/paste

---

## 🛠️ Technology Stack

- **Frontend:** Streamlit (interactive web app)
- **Data:** yfinance (stock prices), RSS feeds (news)
- **AI:** OpenAI GPT-4o-mini (sentiment analysis)
- **Visualization:** Plotly (interactive charts)
- **Backend:** Python 3.9+

---

## 📦 Project Structure

```
llm_momentum_strategy/
├── dashboard.py              # Main Streamlit app
├── run_daily_monitor.py      # Scheduled monitoring script
├── src/
│   ├── monitoring/           # Portfolio tracking, news, alerts
│   ├── automation/           # Daily monitor, email notifier
│   ├── data/                 # Data fetchers (news, analyst, earnings)
│   ├── llm/                  # LLM sentiment scoring
│   └── utils/                # Robinhood CSV parser
├── scripts/                  # Portfolio generation scripts
├── requirements.txt          # Python dependencies
└── .streamlit/
    ├── config.toml          # Streamlit configuration
    └── secrets.toml.example # Secrets template
```

---

## 🌐 Deployment

### Deploy to Streamlit Cloud (FREE)

See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for complete guide.

**Quick steps:**
1. Push to GitHub
2. Go to https://share.streamlit.io
3. Click "New app" → Select your repo → Deploy!

Your app will be live at: `https://your-app-name.streamlit.app`

---

## ⚙️ Configuration

### Required Environment Variables

```bash
# OpenAI API key (required for LLM features)
export OPENAI_API_KEY='sk-...'
```

### Optional: Automated Monitoring

Set up daily automated monitoring with email alerts:

```bash
# Edit run_daily_monitor.py with your settings
python run_daily_monitor.py
```

See [QUICK_START.md](QUICK_START.md) for detailed setup.

---

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md)** - Deploy to production
- **[docs/](docs/)** - Additional guides and documentation

---

## 🤝 Contributing

This is a personal portfolio monitoring tool. Feel free to fork and customize for your own use!

---

## ⚠️ Disclaimer

**This tool is for educational and informational purposes only.**

- Not financial advice
- Past performance does not guarantee future results
- Use at your own risk
- Always do your own research before making investment decisions

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **Streamlit** for amazing web framework
- **yfinance** for stock data
- **Plotly** for interactive charts

---

**Built with ❤️ for smarter portfolio monitoring**

---

## 🔗 Links

- **Dashboard:** Run `streamlit run dashboard.py`
- **Documentation:** See [docs/](docs/) folder
- **Issues:** Report bugs via GitHub Issues

---

*Last updated: November 2025*

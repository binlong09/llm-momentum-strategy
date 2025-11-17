"""
LLM-Enhanced Momentum Strategy Dashboard
Interactive UI for portfolio generation, backtesting, and performance analysis
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(
    page_title="LLM Momentum Strategy",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication (production only - disabled for local development)
from auth import check_authentication, add_logout_button
if not check_authentication():
    st.stop()  # Stop execution if not authenticated

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Choose a view:",
    ["🏠 Overview", "📊 Daily Monitor", "💼 Generate Portfolio", "🔄 Monthly Rebalancing", "🔍 Analyze Individual Stock", "🎯 Robinhood Orders"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Portfolio Stats")

# Load portfolio stats for sidebar
try:
    from src.monitoring import PortfolioTracker
    tracker = PortfolioTracker()
    latest_snapshot = tracker.get_latest_snapshot()

    if latest_snapshot:
        st.sidebar.metric("Portfolio Value", f"${latest_snapshot['total_value']:,.0f}")
        st.sidebar.metric("Holdings", latest_snapshot['num_holdings'])

        # Daily change
        daily_stats = tracker.calculate_daily_change()
        if daily_stats:
            st.sidebar.metric("Daily Change", f"{daily_stats['change_pct']:+.2f}%")
        else:
            st.sidebar.info("Upload portfolio to see stats")
except:
    st.sidebar.info("Upload portfolio to see stats")

# Add logout button (production only)
add_logout_button()

# ============================================================
# PAGE 1: OVERVIEW
# ============================================================
if page == "🏠 Overview":
    st.markdown('<p class="main-header">My Portfolio</p>', unsafe_allow_html=True)
    st.markdown("**Current holdings and performance**")

    st.markdown("---")

    # Import monitoring modules
    try:
        from src.monitoring import PortfolioTracker
        from src.utils.robinhood_export import parse_robinhood_holdings
    except ImportError as e:
        st.error(f"Error importing monitoring modules: {e}")
        st.stop()

    # Initialize tracker
    tracker = PortfolioTracker()

    # Load current portfolio
    holdings_df = tracker.get_current_holdings()
    latest_snapshot = tracker.get_latest_snapshot()

    if latest_snapshot and len(holdings_df) > 0:
        # Portfolio summary metrics
        st.subheader("📊 Portfolio Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
            st.metric("Portfolio Value", f"${latest_snapshot['total_value']:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Number of Holdings", latest_snapshot['num_holdings'])
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            # Calculate daily change if available
            daily_stats = tracker.calculate_daily_change()
            if daily_stats:
                daily_change = daily_stats['change']
                daily_pct = daily_stats['change_pct']
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Daily Change", f"${daily_change:+,.2f}", f"{daily_pct:+.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Daily Change", "N/A", "Need 2+ snapshots")
                st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            # Format timestamp properly
            if isinstance(latest_snapshot['timestamp'], str):
                last_updated = latest_snapshot['timestamp'].split()[0]
            else:
                last_updated = pd.to_datetime(latest_snapshot['timestamp']).strftime('%Y-%m-%d')
            st.metric("Last Updated", last_updated)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Update prices button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Update Prices", use_container_width=True):
                with st.spinner("Fetching latest prices..."):
                    holdings_df = tracker.update_prices(holdings_df)
                    snapshot = tracker.snapshot_portfolio(holdings_df, source="auto")
                    st.success("✅ Prices updated!")
                    st.rerun()

        # Holdings table
        st.subheader("💼 Current Holdings")

        # Prepare display dataframe
        display_df = holdings_df.copy()

        # Sort by market value descending first (before formatting)
        if 'shares' in display_df.columns and 'current_price' in display_df.columns:
            display_df['_sort_value'] = display_df['shares'] * display_df['current_price']
            display_df = display_df.sort_values('_sort_value', ascending=False)
            display_df = display_df.drop('_sort_value', axis=1)

        # Format columns for display
        if 'current_price' in display_df.columns:
            display_df['Current Price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")

        if 'shares' in display_df.columns and 'current_price' in display_df.columns:
            display_df['Market Value'] = (display_df['shares'] * display_df['current_price']).apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
            display_df['Weight'] = (display_df['shares'] * display_df['current_price'] / latest_snapshot['total_value'] * 100).apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")

        if 'price_change_pct' in display_df.columns:
            display_df['Day Change'] = display_df['price_change_pct'].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")

        # Rename for clarity
        display_df = display_df.rename(columns={'symbol': 'Symbol', 'shares': 'Shares'})

        # Select columns to display (after renaming)
        display_cols = ['Symbol']
        if 'Shares' in display_df.columns:
            display_cols.append('Shares')
        if 'Current Price' in display_df.columns:
            display_cols.append('Current Price')
        if 'Market Value' in display_df.columns:
            display_cols.append('Market Value')
        if 'Weight' in display_df.columns:
            display_cols.append('Weight')
        if 'Day Change' in display_df.columns:
            display_cols.append('Day Change')

        # Display
        st.dataframe(
            display_df[display_cols],
            use_container_width=True,
            hide_index=True,
            height=600
        )

        st.markdown("---")

        # Quick actions
        st.subheader("⚡ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**📊 Monitor**")
            st.markdown("Check the [Daily Monitor](#) tab for news and alerts")

        with col2:
            st.markdown("**💼 Rebalance**")
            st.markdown("Use [Monthly Rebalancing](#) to generate new portfolio")

        with col3:
            st.markdown("**🎯 Execute**")
            st.markdown("See [Robinhood Orders](#) for trade instructions")

    else:
        # No portfolio loaded
        st.warning("⚠️ No portfolio data found")
        st.markdown("""
        **Get started:**
        1. Go to the **Daily Monitor** tab
        2. Upload your Robinhood CSV export
        3. Save a snapshot
        4. Return here to see your portfolio overview

        Or use the **Generate Portfolio** tab to create a new portfolio.
        """)

        st.info("💡 **Tip**: Export your holdings from Robinhood to get started!")

# ============================================================
# PAGE 2: DAILY PORTFOLIO MONITOR
# ============================================================
elif page == "📊 Daily Monitor":
    st.markdown('<p class="main-header">Daily Portfolio Monitor</p>', unsafe_allow_html=True)
    st.markdown("Track your portfolio performance, news, and alerts in real-time")

    st.markdown("---")

    # Import monitoring modules
    try:
        from src.monitoring import PortfolioTracker, NewsMonitor, AlertSystem, PerformanceAnalytics
        from src.utils.robinhood_export import parse_robinhood_holdings
    except ImportError as e:
        st.error(f"Error importing monitoring modules: {e}")
        st.stop()

    # Initialize monitoring components
    tracker = PortfolioTracker()
    news_monitor = NewsMonitor()
    alert_system = AlertSystem()
    analytics = PerformanceAnalytics()

    # Upload or select portfolio
    st.subheader("📤 Step 1: Load Your Current Holdings")

    data_source = st.radio(
        "Choose data source:",
        ["📁 Upload Robinhood CSV", "💾 Use Latest Snapshot", "🔄 Update Existing Holdings"]
    )

    holdings_df = None

    if data_source == "📁 Upload Robinhood CSV":
        uploaded_file = st.file_uploader(
            "Upload Robinhood CSV",
            type=['csv'],
            help="Export your holdings from Robinhood"
        )

        if uploaded_file:
            try:
                temp_path = Path("/tmp/robinhood_monitor.csv")
                temp_path.write_bytes(uploaded_file.getvalue())

                holdings_df = parse_robinhood_holdings(str(temp_path))

                st.success(f"✅ Loaded {len(holdings_df)} holdings")

                # Take snapshot
                if st.button("💾 Save Snapshot", help="Save this portfolio state for tracking"):
                    snapshot = tracker.snapshot_portfolio(holdings_df, source="manual")
                    st.success(f"Snapshot saved! Portfolio value: ${snapshot['total_value']:,.2f}")

            except Exception as e:
                st.error(f"Error loading CSV: {e}")

    elif data_source == "💾 Use Latest Snapshot":
        # Load latest snapshot from history
        latest = tracker.get_latest_snapshot()

        if latest:
            st.info(f"📅 Latest snapshot from: {latest['timestamp']}")
            st.metric("Portfolio Value", f"${latest['total_value']:,.2f}")
            st.metric("Number of Holdings", latest['num_holdings'])

            # Get holdings from history
            holdings_df = tracker.get_current_holdings()

            if len(holdings_df) > 0:
                st.success(f"✅ Loaded {len(holdings_df)} holdings from snapshot")

                # Option to update prices
                if st.button("🔄 Update Current Prices"):
                    with st.spinner("Fetching latest prices..."):
                        holdings_df = tracker.update_prices(holdings_df)
                        st.success("Prices updated!")

                        # Take new snapshot with updated prices
                        snapshot = tracker.snapshot_portfolio(holdings_df, source="auto")
                        st.info(f"New snapshot: ${snapshot['total_value']:,.2f}")
            else:
                st.warning("No holdings found in snapshot history")

        else:
            st.warning("⚠️ No snapshots found. Upload a Robinhood CSV to get started.")

    else:  # Update existing
        holdings_df = tracker.get_current_holdings()

        if len(holdings_df) > 0:
            st.info(f"Updating prices for {len(holdings_df)} holdings...")

            with st.spinner("Fetching latest prices..."):
                holdings_df = tracker.update_prices(holdings_df)

            st.success("✅ Prices updated!")

            # Save new snapshot
            snapshot = tracker.snapshot_portfolio(holdings_df, source="auto")
            st.metric("Current Portfolio Value", f"${snapshot['total_value']:,.2f}")
        else:
            st.warning("No existing holdings found. Upload a CSV first.")

    # Display portfolio overview
    if holdings_df is not None and len(holdings_df) > 0:
        st.markdown("---")
        st.subheader("📊 Portfolio Overview")

        # Calculate daily change if possible
        daily_change = tracker.calculate_daily_change()

        if daily_change:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Portfolio Value",
                    f"${daily_change['value_today']:,.2f}",
                    f"{daily_change['change_pct']:.2f}%"
                )

            with col2:
                st.metric(
                    "Daily Change",
                    f"${daily_change['change']:,.2f}",
                    delta_color="normal" if daily_change['change'] >= 0 else "inverse"
                )

            with col3:
                st.metric("Holdings", len(holdings_df))

            with col4:
                # Calculate if we have price changes
                if 'price_change_pct' in holdings_df.columns:
                    avg_change = holdings_df['price_change_pct'].mean()
                    st.metric("Avg Stock Change", f"{avg_change:.2f}%")

        # Top movers
        if 'price_change_pct' in holdings_df.columns:
            st.markdown("### 📈 Top Movers Today")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**🟢 Top Gainers**")
                top_gainers = holdings_df.nlargest(5, 'price_change_pct')
                for _, row in top_gainers.iterrows():
                    st.write(f"**{row['symbol']}**: +{row['price_change_pct']:.2f}%")

            with col2:
                st.markdown("**🔴 Top Losers**")
                top_losers = holdings_df.nsmallest(5, 'price_change_pct')
                for _, row in top_losers.iterrows():
                    st.write(f"**{row['symbol']}**: {row['price_change_pct']:.2f}%")

        # Holdings table
        with st.expander("📋 View All Holdings", expanded=False):
            display_cols = ['symbol', 'shares', 'current_price', 'current_value', 'current_weight']
            display_cols = [c for c in display_cols if c in holdings_df.columns]

            display_df = holdings_df[display_cols].copy()
            if 'current_weight' in display_df.columns:
                display_df['current_weight'] = (display_df['current_weight'] * 100).round(2)
                display_df = display_df.rename(columns={'current_weight': 'weight_%'})

            st.dataframe(display_df, use_container_width=True, hide_index=True)

        # News monitoring
        st.markdown("---")
        st.subheader("📰 News & Alerts")

        if st.button("🔍 Scan News for All Holdings", type="primary"):
            with st.spinner("Scanning news... This may take a minute..."):
                symbols = holdings_df['symbol'].tolist()
                news_df = news_monitor.monitor_holdings(symbols, lookback_days=1, use_llm=False)

                # Generate alerts
                alerts_df = alert_system.generate_alerts(
                    holdings_df=holdings_df,
                    news_monitoring_df=news_df
                )

                # Store in session state
                st.session_state.news_monitoring = news_df
                st.session_state.alerts = alerts_df

            st.success("✅ News scan complete!")

        # Display alerts if available
        if 'alerts' in st.session_state and len(st.session_state.alerts) > 0:
            alerts_df = st.session_state.alerts

            # Alert summary
            summary = alert_system.summarize_alerts(alerts_df)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🚨 Critical", summary['critical'])

            with col2:
                st.metric("⚠️ Warnings", summary['warnings'])

            with col3:
                st.metric("ℹ️ Info", summary['info'])

            # Critical alerts (if any)
            critical = alert_system.get_critical_actions(alerts_df)
            if len(critical) > 0:
                st.error("🚨 **CRITICAL ALERTS - IMMEDIATE ACTION REQUIRED**")

                for _, alert in critical.iterrows():
                    with st.container():
                        st.markdown(f"### {alert['symbol']}")
                        st.markdown(f"**{alert['message']}**")
                        st.markdown(f"📝 Action: {alert['action']}")
                        st.markdown("---")

            # All alerts
            with st.expander("📋 View All Alerts", expanded=len(critical) == 0):
                for _, alert in alerts_df.iterrows():
                    severity_color = {
                        'critical': '🚨',
                        'warning': '⚠️',
                        'info': 'ℹ️'
                    }

                    emoji = severity_color.get(alert['severity'], '•')

                    st.markdown(f"{emoji} **{alert['symbol']}** - {alert['message']}")
                    st.caption(f"Action: {alert['action']}")

        # News details
        if 'news_monitoring' in st.session_state:
            news_df = st.session_state.news_monitoring

            with st.expander("📰 Detailed News Analysis", expanded=False):
                # Filter options
                filter_type = st.selectbox(
                    "Filter by:",
                    ["All", "Critical", "Warnings", "Positive", "Neutral"]
                )

                if filter_type != "All":
                    filter_map = {
                        "Critical": "critical",
                        "Warnings": "warning",
                        "Positive": ["positive", "very_positive"],
                        "Neutral": "neutral"
                    }
                    filter_val = filter_map[filter_type]

                    if isinstance(filter_val, list):
                        filtered_news = news_df[news_df['sentiment'].isin(filter_val)]
                    elif filter_type in ["Critical", "Warnings"]:
                        filtered_news = news_df[news_df['alert_level'] == filter_val]
                    else:
                        filtered_news = news_df[news_df['sentiment'] == filter_val]
                else:
                    filtered_news = news_df

                # Display news
                for _, row in filtered_news.iterrows():
                    sentiment_emoji = {
                        'very_positive': '🟢',
                        'positive': '🟢',
                        'neutral': '⚪',
                        'negative': '🟡',
                        'very_negative': '🔴'
                    }

                    emoji = sentiment_emoji.get(row['sentiment'], '⚪')

                    st.markdown(f"{emoji} **{row['symbol']}** ({row['num_articles']} articles)")
                    st.caption(row['summary'])

                    # Show evidence for alerts with justification
                    has_evidence = False

                    # Red flag evidence
                    red_flag_evidence = row.get('red_flag_evidence')
                    if isinstance(red_flag_evidence, list) and len(red_flag_evidence) > 0:
                        has_evidence = True
                        with st.expander(f"🚨 Red Flag Evidence ({len(row['red_flag_evidence'])} items)", expanded=False):
                            for evidence in row['red_flag_evidence']:
                                st.markdown(f"**Keyword:** `{evidence['keyword']}` (Relevance: {evidence.get('relevance', 'N/A')})")
                                st.markdown(f"**Article:** {evidence['article_title']}")
                                st.caption(f"*Context:* ...{evidence['context']}...")
                                st.caption(f"Published: {evidence['published']}")
                                if evidence.get('url'):
                                    st.markdown(f"[🔗 Read full article]({evidence['url']})")
                                st.markdown("---")

                    # Warning evidence
                    warning_evidence = row.get('warning_evidence')
                    if isinstance(warning_evidence, list) and len(warning_evidence) > 0:
                        has_evidence = True
                        with st.expander(f"⚠️ Warning Evidence ({len(row['warning_evidence'])} items)", expanded=False):
                            for evidence in row['warning_evidence']:
                                st.markdown(f"**Keyword:** `{evidence['keyword']}`")
                                st.markdown(f"**Article:** {evidence['article_title']}")
                                st.caption(f"*Context:* ...{evidence['context']}...")
                                st.caption(f"Published: {evidence['published']}")
                                if evidence.get('url'):
                                    st.markdown(f"[🔗 Read full article]({evidence['url']})")
                                st.markdown("---")

                    # Positive evidence
                    positive_evidence = row.get('positive_evidence')
                    if isinstance(positive_evidence, list) and len(positive_evidence) > 0:
                        has_evidence = True
                        with st.expander(f"✅ Positive Evidence ({len(row['positive_evidence'])} items)", expanded=False):
                            for evidence in row['positive_evidence']:
                                st.markdown(f"**Keyword:** `{evidence['keyword']}`")
                                st.markdown(f"**Article:** {evidence['article_title']}")
                                st.caption(f"*Context:* ...{evidence['context']}...")
                                st.caption(f"Published: {evidence['published']}")
                                if evidence.get('url'):
                                    st.markdown(f"[🔗 Read full article]({evidence['url']})")
                                st.markdown("---")

                    # Fallback to latest article if no evidence
                    if not has_evidence and row.get('latest_url'):
                        st.caption(f"[Read latest article]({row['latest_url']})")

                    st.markdown("---")

        # Performance analytics
        st.markdown("---")
        st.subheader("📈 Performance Analytics")

        # Period selection
        period = st.selectbox(
            "Select period:",
            ["7 Days", "30 Days", "90 Days", "All Time"]
        )

        period_days = {
            "7 Days": 7,
            "30 Days": 30,
            "90 Days": 90,
            "All Time": 365 * 10
        }[period]

        # Get historical snapshots
        snapshots_df = tracker.get_snapshots(days=period_days)

        if len(snapshots_df) >= 2:
            # Calculate metrics
            metrics = analytics.calculate_metrics(snapshots_df, benchmark_symbol='SPY')

            if 'error' not in metrics:
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Return", f"{metrics['total_return']*100:.2f}%")

                with col2:
                    st.metric("Annualized Return", f"{metrics['annualized_return']*100:.2f}%")

                with col3:
                    st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")

                with col4:
                    st.metric("Max Drawdown", f"{metrics['max_drawdown']*100:.2f}%")

                # Benchmark comparison
                if metrics.get('benchmark'):
                    st.markdown("### 📊 vs S&P 500")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Your Return", f"{metrics['annualized_return']*100:.2f}%")

                    with col2:
                        st.metric("S&P 500 Return", f"{metrics['benchmark']['annualized_return']*100:.2f}%")

                    with col3:
                        alpha = metrics['alpha']
                        st.metric("Alpha", f"{alpha*100:.2f}%", delta_color="normal" if alpha >= 0 else "inverse")

                # Performance chart
                st.markdown("### 📈 Portfolio Value Over Time")

                chart_data = snapshots_df[['date', 'total_value']].copy()
                chart_data = chart_data.set_index('date')

                st.line_chart(chart_data)

                # Performance report
                with st.expander("📄 Full Performance Report", expanded=False):
                    report = analytics.generate_performance_report(metrics, f"{period} Performance")
                    st.code(report, language="")

            else:
                st.warning(f"Cannot calculate metrics: {metrics['error']}")

        else:
            st.info(f"Need at least 2 snapshots to calculate performance. Current: {len(snapshots_df)}")
            st.caption("Upload your portfolio daily to track performance over time.")

        # Quick actions
        st.markdown("---")
        st.subheader("⚡ Quick Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Deep Dive on Stock"):
                st.info("Switch to '🔍 Analyze Individual Stock' page to research specific holdings")

        with col2:
            if st.button("📊 View Full Portfolio"):
                st.info("Go to '💼 Generate Portfolio' page to see full portfolio details")

        with col3:
            if st.button("🔄 Rebalance Now"):
                st.info("Go to '🔄 Monthly Rebalancing' page to compare with new portfolio")

    else:
        st.info("👆 Upload your Robinhood CSV or load a snapshot to get started")

        st.markdown("""
        ### 🚀 Getting Started

        **First time?**
        1. Export your current holdings from Robinhood (CSV format)
        2. Upload it above
        3. Click "Save Snapshot" to start tracking
        4. Come back daily to monitor performance and news

        **Daily routine:**
        1. Click "Update Existing Holdings" to refresh prices
        2. Scan news for any alerts
        3. Review performance vs S&P 500
        4. Take action only on critical alerts
        """)

# ============================================================
# PAGE 3: GENERATE PORTFOLIO
# ============================================================
elif page == "💼 Generate Portfolio":
    st.markdown('<p class="main-header">Generate Current Portfolio</p>', unsafe_allow_html=True)
    st.markdown("Configure parameters and generate your monthly portfolio recommendations")

    st.markdown("---")

    # Initialize session state for portfolio data
    if 'portfolio_df' not in st.session_state:
        st.session_state.portfolio_df = None

    # Configuration options
    col1, col2, col3 = st.columns(3)

    with col1:
        portfolio_size = st.slider("Portfolio Size", 20, 100, 50, 5)
        st.caption("Number of stocks in final portfolio")

    with col2:
        weighting = st.selectbox("Base Weighting", ["equal", "momentum", "inverse_vol"])
        st.caption("How to weight stocks before LLM tilting")

    with col3:
        use_llm = st.checkbox("Use LLM Enhancement", value=True)
        st.caption("Enable LLM scoring")

    if use_llm:
        col1, col2, col3 = st.columns(3)

        with col1:
            tilt_factor = st.slider("LLM Tilting Factor (η)", 1.0, 10.0, 5.0, 0.5)
            st.caption(f"Higher = more concentration on high-scoring stocks (paper optimal: 5.0)")

        with col2:
            enable_risk_scoring = st.checkbox("Add Risk Scores", value=False)
            st.caption("Analyze individual stock risk using LLM")

        # Add prompt viewing option
        store_llm_prompts = st.checkbox("📝 Store LLM Prompts", value=False, help="Save prompts to review what the LLM analyzed")
        if store_llm_prompts:
            st.caption("💡 You'll be able to view exact prompts sent to LLM for each stock")
            if enable_risk_scoring:
                st.caption("✅ Both LLM scoring and risk scoring prompts will be stored")
            else:
                st.caption("ℹ️ Only LLM scoring prompts will be stored (enable 'Add Risk Scores' to see risk prompts too)")

        # Add research mode option (Hybrid Approach)
        enable_research_mode = st.checkbox(
            "🔬 Generate Detailed Explanations",
            value=False,
            help="Generate AI analysis for top holdings (adds 30-60 seconds)"
        )
        if enable_research_mode:
            num_research_stocks = st.slider(
                "Number of stocks to explain",
                5, 20, 10, 1,
                help="Generate detailed AI analysis for your top N holdings"
            )
            st.caption(f"💡 Will generate 3-5 sentence AI analysis for top {num_research_stocks} holdings")
            st.caption(f"⏱️ Adds ~{num_research_stocks * 2}-{num_research_stocks * 4} seconds to generation time")
        else:
            num_research_stocks = 10

        with col3:
            model_options = {
                "GPT-4o-mini (Default, $0.08/year)": "gpt-4o-mini",
                "GPT-4o (Better, $1.35/year)": "gpt-4o",
                "GPT-4 Turbo (Best, $4.80/year)": "gpt-4-turbo",
                "GPT-4o Latest (Nov 2024)": "gpt-4o-2024-11-20"
            }
            selected_model_display = st.selectbox(
                "LLM Model",
                options=list(model_options.keys()),
                index=0
            )
            model = model_options[selected_model_display]

            # Show cost comparison
            if model == "gpt-4o-mini":
                st.caption("💰 Most cost-effective, 90% performance")
            elif model == "gpt-4o":
                st.caption("💰 Best cost/performance balance")
            elif model == "gpt-4-turbo":
                st.caption("🚀 Maximum performance, 59x more expensive")
            else:
                st.caption("🆕 Latest GPT-4o model")
        # Risk scoring options (only show if risk scoring is enabled)
        if enable_risk_scoring:
            with st.expander("⚙️ Risk Scoring Settings", expanded=False):
                st.markdown("**Adjust high-risk positions:**")

                apply_risk_adjustment = st.checkbox(
                    "Reduce weights for high-risk stocks",
                    value=False,
                    help="Automatically reduce position sizes for stocks with high risk scores"
                )

                if apply_risk_adjustment:
                    col1, col2 = st.columns(2)
                    with col1:
                        risk_threshold = st.slider(
                            "Risk Threshold",
                            0.5, 0.9, 0.7, 0.05,
                            help="Risk score above which to reduce weights"
                        )
                    with col2:
                        risk_reduction_factor = st.slider(
                            "Reduction Factor",
                            0.2, 0.8, 0.5, 0.1,
                            help="Multiply high-risk weights by this factor"
                        )

                    st.caption(f"Stocks with risk > {risk_threshold} will have weights reduced to {risk_reduction_factor*100:.0f}%")
                else:
                    risk_threshold = None
                    risk_reduction_factor = None
        else:
            apply_risk_adjustment = False
            risk_threshold = None
            risk_reduction_factor = None

    else:
        tilt_factor = 0.0
        model = None
        enable_risk_scoring = False
        apply_risk_adjustment = False
        risk_threshold = None
        risk_reduction_factor = None

    st.markdown("---")

    # Volatility Protection Section
    st.subheader("🛡️ Volatility Protection (NEW!)")

    col1, col2 = st.columns([1, 2])

    with col1:
        enable_protection = st.checkbox("Enable Volatility Protection", value=False)
        st.caption("Reduces exposure during volatile markets")

    with col2:
        if enable_protection:
            st.info("📊 This will adjust portfolio exposure based on VIX levels and market regime")
        else:
            st.warning("⚠️ No protection - portfolio maintains full exposure in all market conditions")

    # Protection configuration (only show if enabled)
    if enable_protection:
        with st.expander("⚙️ Advanced Protection Settings", expanded=False):
            st.markdown("**Risk Profile:**")

            risk_profile = st.select_slider(
                "Select your risk tolerance",
                options=["Conservative", "Balanced", "Aggressive"],
                value="Balanced"
            )

            # Preset configurations
            if risk_profile == "Conservative":
                vix_high = 25.0
                vix_panic = 35.0
                target_vol = 0.10
                st.caption("✅ Lower VIX thresholds, 10% target volatility - Earlier protection")
            elif risk_profile == "Aggressive":
                vix_high = 35.0
                vix_panic = 45.0
                target_vol = 0.20
                st.caption("✅ Higher VIX thresholds, 20% target volatility - Less frequent protection")
            else:  # Balanced
                vix_high = 30.0
                vix_panic = 40.0
                target_vol = 0.15
                st.caption("✅ Moderate thresholds, 15% target volatility - Recommended for most")

            st.markdown("---")
            st.markdown("**Custom Thresholds (Optional):**")

            col1, col2, col3 = st.columns(3)
            with col1:
                vix_high = st.number_input("VIX High Threshold", 15.0, 50.0, vix_high, 1.0)
            with col2:
                vix_panic = st.number_input("VIX Panic Threshold", 25.0, 80.0, vix_panic, 1.0)
            with col3:
                target_vol = st.number_input("Target Volatility", 0.05, 0.30, target_vol, 0.01)

            st.caption(f"📌 Current: VIX>{vix_high:.0f}=high risk, VIX>{vix_panic:.0f}=panic, target={target_vol:.0%} vol")
    else:
        vix_high = None
        vix_panic = None
        target_vol = None

    st.markdown("---")

    # Debug: Show current checkbox states
    if use_llm and store_llm_prompts:
        with st.expander("🔧 Debug: Checkbox States", expanded=False):
            st.write(f"**Use LLM:** {use_llm}")
            st.write(f"**Store Prompts:** {store_llm_prompts}")
            st.write(f"**Enable Risk Scoring:** {enable_risk_scoring if 'enable_risk_scoring' in locals() else 'Not defined'}")
            st.write(f"**Apply Risk Adjustment:** {apply_risk_adjustment if 'apply_risk_adjustment' in locals() else 'Not defined'}")

    # Generate button
    if st.button("🔄 Generate Portfolio", type="primary"):
        # Show which model is being used
        if use_llm:
            model_display = {
                "gpt-4o-mini": "GPT-4o-mini",
                "gpt-4o": "GPT-4o",
                "gpt-4-turbo": "GPT-4 Turbo",
                "gpt-4o-2024-11-20": "GPT-4o (Nov 2024)"
            }.get(model, model)
            st.info(f"🤖 Using {model_display} for LLM scoring...")

        if enable_protection:
            st.info(f"🛡️ Volatility protection enabled ({risk_profile} profile)")

        with st.spinner("Generating portfolio... This may take 1-2 minutes for LLM scoring..."):
            try:
                # Import and run portfolio generation
                from scripts.generate_portfolio import generate_current_portfolio

                result = generate_current_portfolio(
                    portfolio_size=portfolio_size,
                    base_weighting=weighting,
                    use_llm=use_llm,
                    tilt_factor=tilt_factor,
                    model=model if use_llm else None,
                    export_csv=True,
                    enable_protection=enable_protection,
                    vix_high=vix_high,
                    vix_panic=vix_panic,
                    target_vol=target_vol,
                    enable_risk_scoring=enable_risk_scoring,
                    apply_risk_adjustment=apply_risk_adjustment,
                    risk_threshold=risk_threshold,
                    risk_reduction_factor=risk_reduction_factor,
                    store_prompts=store_llm_prompts if use_llm else False,
                    enable_research_mode=enable_research_mode if use_llm else False,
                    num_research_stocks=num_research_stocks
                )

                # Handle return value (either portfolio or (portfolio, prompt_store))
                if use_llm and store_llm_prompts and isinstance(result, tuple):
                    portfolio_df, prompt_store = result
                    st.session_state.prompt_store = prompt_store
                else:
                    portfolio_df = result
                    st.session_state.prompt_store = None

                # Store in session state
                st.session_state.portfolio_df = portfolio_df
                st.session_state.model_used = model if use_llm else "baseline"
                st.session_state.protection_enabled = enable_protection

                success_msg = f"✅ Portfolio generated successfully with {model_display if use_llm else 'baseline momentum'}!"
                if use_llm and store_llm_prompts:
                    success_msg += " (Prompts stored for review)"
                    if enable_risk_scoring:
                        success_msg += " - Including risk prompts"
                    else:
                        success_msg += " - LLM prompts only (risk scoring was disabled)"
                st.success(success_msg)

                # Debug info
                if use_llm and store_llm_prompts:
                    with st.expander("🔍 Generation Details", expanded=False):
                        st.write(f"**LLM Enabled:** {use_llm}")
                        st.write(f"**Prompts Stored:** {store_llm_prompts}")
                        st.write(f"**Risk Scoring Enabled:** {enable_risk_scoring}")
                        if st.session_state.prompt_store:
                            summary = st.session_state.prompt_store.get_session_summary()
                            st.write(f"**Stocks in prompt store:** {summary['stock_count']}")
                            st.write(f"**Prompt types stored:** {summary['prompt_types']}")
                        else:
                            st.write("**Prompt store:** Not available")

            except Exception as e:
                st.error(f"❌ Error generating portfolio: {str(e)}")
                st.exception(e)
                st.session_state.portfolio_df = None

    # Display results from session state (persists across reruns)
    if st.session_state.portfolio_df is not None:
        portfolio_df = st.session_state.portfolio_df

        # Add ranking explanations
        from src.utils import add_ranking_explanations, generate_stock_justification, generate_portfolio_summary

        portfolio_df = add_ranking_explanations(portfolio_df)

        # Portfolio summary
        st.markdown("---")
        st.subheader("📊 Portfolio Overview")

        summary_text = generate_portfolio_summary(portfolio_df)
        st.markdown(summary_text)

        # Display top holdings
        st.markdown("---")
        st.subheader(f"📋 Portfolio Holdings ({len(portfolio_df)} stocks)")

        # Format the dataframe for display
        display_df = portfolio_df.copy()
        display_df['weight'] = (display_df['weight'] * 100).round(2).astype(str) + '%'
        display_df['momentum_return'] = (display_df['momentum_return'] * 100).round(2).astype(str) + '%'
        if 'llm_score' in display_df.columns:
            display_df['llm_score'] = display_df['llm_score'].round(3)

        # Add risk score formatting if available
        if 'risk_score' in display_df.columns:
            display_df['risk_score'] = display_df['risk_score'].round(2)

            # Color code risk scores
            def color_risk_score(val):
                try:
                    score = float(val)
                    if score < 0.4:
                        return 'background-color: #d4edda'  # Light green (low risk)
                    elif score < 0.7:
                        return 'background-color: #fff3cd'  # Light yellow (medium risk)
                    else:
                        return 'background-color: #f8d7da'  # Light red (high risk)
                except:
                    return ''

        # Add header row for the columns
        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6, header_col7 = st.columns([0.8, 1.5, 1.2, 1.3, 1.3, 1.5, 4.5])
        with header_col1:
            st.markdown("**Rank**")
        with header_col2:
            st.markdown("**Symbol**")
        with header_col3:
            st.markdown("**Weight**")
        with header_col4:
            st.markdown("**12M Return**")
        with header_col5:
            st.markdown("**AI Score**")
        with header_col6:
            st.markdown("**Risk**")
        with header_col7:
            st.markdown("**Summary**")
        st.markdown("---")

        # Display table with expandable rows
        for rank, (idx, row) in enumerate(portfolio_df.iterrows(), start=1):
            # Get justification
            justification_data = generate_stock_justification(row, rank, len(portfolio_df))

            # Create expander for each stock with more detailed columns
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.8, 1.5, 1.2, 1.3, 1.3, 1.5, 4.5])

            with col1:
                st.write(f"**#{rank}**")
            with col2:
                st.write(f"**{row['symbol']}**")
            with col3:
                st.write(f"{row['weight']*100:.2f}%")
            with col4:
                # Momentum return with color coding
                momentum_return = row['momentum_return'] * 100
                if momentum_return >= 50:
                    st.markdown(f"🟢 **{momentum_return:.1f}%**")
                elif momentum_return >= 20:
                    st.markdown(f"🟡 {momentum_return:.1f}%")
                else:
                    st.markdown(f"🔴 {momentum_return:.1f}%")
            with col5:
                # LLM Score if available
                if 'llm_score' in row and pd.notna(row['llm_score']):
                    llm_score = row['llm_score']
                    if llm_score >= 0.7:
                        st.markdown(f"🟢 **{llm_score:.2f}**")
                    elif llm_score >= 0.5:
                        st.markdown(f"🟡 {llm_score:.2f}")
                    else:
                        st.markdown(f"🔴 {llm_score:.2f}")
                else:
                    st.write("—")
            with col6:
                # Risk Score if available
                if 'risk_score' in row and pd.notna(row['risk_score']):
                    risk_score = row['risk_score']
                    if risk_score < 0.4:
                        st.markdown(f"🟢 **{risk_score:.2f}**")
                    elif risk_score < 0.7:
                        st.markdown(f"🟡 {risk_score:.2f}")
                    else:
                        st.markdown(f"🔴 {risk_score:.2f}")
                else:
                    st.write("—")
            with col7:
                st.write(justification_data['summary'])

            # Expandable details
            with st.expander(f"📊 View detailed analysis for {row['symbol']}", expanded=False):
                # Show AI analysis if available (from research mode)
                if 'ai_analysis' in portfolio_df.columns and row.get('ai_analysis'):
                    st.markdown("### 🔬 AI Analysis (Research Mode)")
                    st.info(row['ai_analysis'])
                    st.markdown("---")

                # Show justification
                st.markdown(justification_data['justification'])

                # Show LLM prompts if available
                if st.session_state.get('prompt_store') is not None:
                    st.markdown("---")
                    prompt_store = st.session_state.prompt_store

                    # Get all available prompts for this stock
                    all_prompts = prompt_store.get_all_prompts(row['symbol'])

                    # LLM Scoring Prompt
                    if 'llm_scoring' in all_prompts:
                        with st.expander("📝 View LLM Scoring Prompt (momentum analysis)", expanded=False):
                            llm_prompt = all_prompts['llm_scoring']
                            st.markdown("**This is what was sent to the LLM for momentum scoring:**")
                            st.code(llm_prompt, language="text")
                            st.caption(f"📏 Prompt length: {len(llm_prompt)} characters")

                    # Risk Scoring Prompt
                    if 'risk_scoring' in all_prompts:
                        with st.expander("🔍 View Risk Scoring Prompt (risk analysis)", expanded=False):
                            risk_prompt = all_prompts['risk_scoring']
                            st.markdown("**This is what was sent to the LLM for risk assessment:**")
                            st.code(risk_prompt, language="text")
                            st.caption(f"📏 Prompt length: {len(risk_prompt)} characters")
                    elif 'llm_scoring' in all_prompts:
                        # LLM prompts stored but no risk prompts - show helpful message
                        with st.expander("🔍 Risk Scoring Prompt not available", expanded=False):
                            st.info("💡 **To see risk prompts:** Enable both '📝 Store LLM Prompts' AND 'Add Risk Scores' when generating portfolio")

                    # Show info if no prompts stored
                    if not all_prompts:
                        with st.expander("📝 No prompts stored", expanded=False):
                            st.info("Enable '📝 Store LLM Prompts' when generating to see prompts here")

                # Show metrics in columns
                st.markdown("---")
                st.markdown("**Quick Metrics**:")

                metric_cols = st.columns(4)
                with metric_cols[0]:
                    st.metric("Momentum", justification_data['momentum_rating'])
                with metric_cols[1]:
                    if justification_data['llm_rating'] != 'N/A':
                        st.metric("AI Sentiment", justification_data['llm_rating'])
                with metric_cols[2]:
                    if justification_data['risk_rating'] != 'N/A':
                        st.metric("Risk Level", justification_data['risk_rating'])
                with metric_cols[3]:
                    st.metric("Percentile", f"{justification_data['percentile']:.0f}%")

        st.markdown("---")

        # Add legend
        st.caption("**Legend:** 🟢 Good/Low Risk | 🟡 Moderate | 🔴 Weak/High Risk | — Not Available")
        st.caption("💡 **Tip:** Click 'View detailed analysis' on any stock to see full justification, metrics, and LLM prompts")

        # Volatility Protection Status (if enabled)
        if st.session_state.get('protection_enabled', False) and 'protection_regime' in portfolio_df.columns:
            st.markdown("---")
            st.subheader("🛡️ Volatility Protection Status")

            regime = portfolio_df['protection_regime'].iloc[0]
            exposure = portfolio_df['protection_exposure'].iloc[0]
            cash_position = 1.0 - portfolio_df['weight'].sum()

            # Color code based on regime
            regime_colors = {
                'bull': '🟢',
                'normal': '🟡',
                'volatile': '🟠',
                'bear': '🔴',
                'panic': '⚫'
            }
            regime_icon = regime_colors.get(regime, '⚪')

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Market Regime",
                    f"{regime_icon} {regime.upper()}",
                    help="Current market state based on VIX and price trends"
                )
            with col2:
                delta_exposure = (exposure - 1.0) * 100
                st.metric(
                    "Portfolio Exposure",
                    f"{exposure:.1%}",
                    f"{delta_exposure:+.1f}%",
                    delta_color="inverse"
                )
            with col3:
                st.metric(
                    "Cash Position",
                    f"{cash_position:.1%}",
                    help="Percentage of portfolio held in cash for protection"
                )

            # Protection recommendation
            if exposure < 0.5:
                st.error(f"⚠️ **HIGH RISK DETECTED** - Exposure reduced to {exposure:.0%}. Consider moving to cash or bonds.")
            elif exposure < 0.75:
                st.warning(f"⚡ **ELEVATED RISK** - Exposure reduced to {exposure:.0%}. Monitor markets closely.")
            elif exposure < 0.9:
                st.info(f"📊 **NORMAL PROTECTION** - Slight exposure reduction to {exposure:.0%}.")
            else:
                st.success(f"✅ **FAVORABLE CONDITIONS** - Near full exposure at {exposure:.0%}.")

        # Risk Score Distribution (if enabled)
        if 'risk_score' in portfolio_df.columns:
            st.markdown("---")
            st.subheader("📊 Risk Score Distribution")

            low_risk_count = (portfolio_df['risk_score'] <= 0.4).sum()
            medium_risk_count = ((portfolio_df['risk_score'] > 0.4) & (portfolio_df['risk_score'] <= 0.7)).sum()
            high_risk_count = (portfolio_df['risk_score'] > 0.7).sum()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "🟢 Low Risk",
                    f"{low_risk_count} stocks",
                    f"{low_risk_count/len(portfolio_df)*100:.1f}%",
                    help="Risk score 0.0-0.4"
                )
            with col2:
                st.metric(
                    "🟡 Medium Risk",
                    f"{medium_risk_count} stocks",
                    f"{medium_risk_count/len(portfolio_df)*100:.1f}%",
                    help="Risk score 0.4-0.7"
                )
            with col3:
                st.metric(
                    "🔴 High Risk",
                    f"{high_risk_count} stocks",
                    f"{high_risk_count/len(portfolio_df)*100:.1f}%",
                    help="Risk score 0.7-1.0"
                )

            # High risk warnings
            if high_risk_count > 0:
                st.warning(f"⚠️ **{high_risk_count} high-risk stocks detected** - Consider monitoring closely or reducing exposure")

                high_risk_stocks = portfolio_df[portfolio_df['risk_score'] > 0.7].head(5)
                if len(high_risk_stocks) > 0:
                    with st.expander(f"View High-Risk Stocks ({len(high_risk_stocks)})", expanded=False):
                        risk_display = high_risk_stocks[['symbol', 'weight', 'risk_score', 'key_risk']].copy()
                        risk_display['weight'] = (risk_display['weight'] * 100).round(2).astype(str) + '%'
                        risk_display['risk_score'] = risk_display['risk_score'].round(2)
                        st.dataframe(risk_display, use_container_width=True, hide_index=True)

        # Robinhood Export Section
        st.markdown("---")
        st.subheader("📤 Export for Robinhood Trading")

        with st.expander("🎯 Export Portfolio for Manual Trading", expanded=False):
            st.markdown("""
            **Export your top holdings in a format optimized for manual trading on Robinhood.**

            This feature lets you:
            - Select how many stocks to trade (e.g., top 20)
            - Exclude stocks you don't like (auto-fills with #21, #22, etc.)
            - Calculate $ amounts for each stock
            - Get step-by-step trading instructions
            """)

            col1, col2 = st.columns(2)

            with col1:
                num_export_stocks = st.number_input(
                    "Number of stocks to trade",
                    min_value=5,
                    max_value=min(50, len(portfolio_df)),
                    value=min(20, len(portfolio_df)),
                    step=1,
                    help="Select top N stocks from your portfolio"
                )

            with col2:
                total_investment = st.number_input(
                    "Total investment amount ($)",
                    min_value=100.0,
                    max_value=1000000.0,
                    value=10000.0,
                    step=1000.0,
                    help="How much $ you want to invest in total"
                )

            # Stock exclusion
            available_symbols = portfolio_df.head(num_export_stocks + 10)['symbol'].tolist()
            excluded_stocks = st.multiselect(
                "⚠️ Exclude stocks (optional)",
                options=available_symbols,
                default=[],
                help="Don't like a stock? Exclude it and we'll auto-fill with the next ranked stock"
            )

            if st.button("📥 Generate Robinhood Export", type="primary"):
                try:
                    from src.utils.robinhood_export import export_for_robinhood, generate_trading_instructions

                    # Generate export
                    trading_df, filepath = export_for_robinhood(
                        portfolio_df=portfolio_df,
                        num_stocks=num_export_stocks,
                        exclude_symbols=excluded_stocks,
                        total_investment=total_investment,
                        output_dir="results/exports"
                    )

                    st.success(f"✅ Export generated successfully!")

                    # Show preview
                    st.markdown("### 📊 Trading Preview")
                    st.dataframe(trading_df, use_container_width=True, hide_index=True)

                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Stocks to Buy", len(trading_df))
                    with col2:
                        st.metric("Total Investment", f"${total_investment:,.0f}")
                    with col3:
                        avg_per_stock = total_investment / len(trading_df)
                        st.metric("Avg per Stock", f"${avg_per_stock:,.0f}")
                    with col4:
                        if excluded_stocks:
                            st.metric("Excluded", len(excluded_stocks))

                    if excluded_stocks:
                        st.info(f"✅ Excluded: {', '.join(excluded_stocks)} → Auto-filled with next ranked stocks")

                    # Download button
                    st.markdown("---")
                    st.markdown("### 💾 Download & Instructions")

                    with open(filepath, 'r') as f:
                        csv_data = f.read()

                    st.download_button(
                        label="📥 Download CSV for Trading",
                        data=csv_data,
                        file_name=filepath.split('/')[-1],
                        mime='text/csv',
                        help="Download this file and use it as reference when placing orders on Robinhood"
                    )

                    # Trading instructions
                    instructions = generate_trading_instructions(
                        trading_df=trading_df,
                        total_investment=total_investment,
                        excluded_stocks=excluded_stocks
                    )

                    with st.expander("📖 Step-by-Step Trading Instructions", expanded=True):
                        st.code(instructions, language="text")

                except Exception as e:
                    st.error(f"❌ Export failed: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # Portfolio summary
        st.markdown("---")
        st.subheader("📊 Portfolio Summary")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Positions", len(portfolio_df))
        with col2:
            st.metric("Max Weight", f"{portfolio_df['weight'].max()*100:.2f}%")
        with col3:
            st.metric("Min Weight", f"{portfolio_df['weight'].min()*100:.2f}%")
        with col4:
            avg_score = portfolio_df['llm_score'].mean() if 'llm_score' in portfolio_df.columns else 0
            st.metric("Avg LLM Score", f"{avg_score:.3f}")
        with col5:
            model_used = st.session_state.get('model_used', 'baseline')
            model_display = {
                "gpt-4o-mini": "4o-mini",
                "gpt-4o": "4o",
                "gpt-4-turbo": "4-Turbo",
                "gpt-4o-2024-11-20": "4o-Nov",
                "baseline": "None"
            }.get(model_used, model_used)
            st.metric("Model Used", model_display)

        # Download button
        st.markdown("---")
        csv = portfolio_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Portfolio CSV",
            data=csv,
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

        # Position sizing calculator
        st.markdown("---")
        st.subheader("💰 Position Sizing Calculator")

        capital = st.number_input("Portfolio Capital ($)", 10000, 10000000, 100000, 10000)

        st.markdown("**Top 10 Positions:**")
        sizing_df = portfolio_df.head(10).copy()
        sizing_df['position_value'] = (sizing_df['weight'] * capital).round(2)
        sizing_df['position_value_str'] = sizing_df['position_value'].apply(lambda x: f"${x:,.2f}")
        sizing_df['weight_pct'] = (sizing_df['weight'] * 100).round(2).astype(str) + '%'

        display_sizing = sizing_df[['symbol', 'weight_pct', 'position_value_str']].copy()
        display_sizing.columns = ['Symbol', 'Weight', 'Position Value']
        st.dataframe(display_sizing, use_container_width=True, hide_index=True)

    else:
        st.info("👆 Configure parameters above and click 'Generate Portfolio' to create your monthly recommendations")

        # Show example of what output looks like
        st.markdown("---")
        st.subheader("📝 Example Output")

        example_data = {
            'symbol': ['KKR', 'HWM', 'LLY', 'IRM', 'KLAC'],
            'weight': ['14.43%', '14.43%', '14.43%', '4.73%', '4.73%'],
            'momentum_return': ['97.05%', '95.39%', '73.23%', '78.25%', '63.28%'],
            'llm_score': [1.000, 1.000, 1.000, 0.600, 0.600]
        }
        st.dataframe(pd.DataFrame(example_data), use_container_width=True, hide_index=True)

# ============================================================
# PAGE 3: MONTHLY REBALANCING
# ============================================================
elif page == "🔄 Monthly Rebalancing":
    st.markdown('<p class="main-header">Monthly Portfolio Rebalancing</p>', unsafe_allow_html=True)
    st.markdown("Compare your current holdings with a new portfolio and get exact rebalancing instructions")

    st.markdown("---")

    st.markdown("""
    ### 📋 How It Works

    1. **Upload Current Holdings** - Export CSV from Robinhood and upload here
    2. **Select New Portfolio** - Choose a saved portfolio or generate a new one
    3. **Review Changes** - See what needs to be sold, bought, or rebalanced
    4. **Get Instructions** - Download step-by-step trading guide for Robinhood

    **When to rebalance:** Once per month on the same day (e.g., first Monday of each month)
    """)

    st.markdown("---")

    # Step 1: Upload current holdings
    st.subheader("📤 Step 1: Upload Current Holdings")

    st.markdown("""
    **How to export from Robinhood:**
    - **Mobile App:** Account → Menu (☰) → Statements & History → Account Statements → Export
    - **Website:** Account → History → Download

    Make sure the CSV includes: Symbol, Quantity, Current Price
    """)

    uploaded_holdings = st.file_uploader(
        "Upload Robinhood Holdings CSV",
        type=['csv'],
        help="Export your current holdings from Robinhood"
    )

    current_holdings_df = None
    total_portfolio_value = 0

    if uploaded_holdings:
        try:
            from src.utils.robinhood_export import parse_robinhood_holdings

            # Save uploaded file temporarily
            temp_path = Path("/tmp/robinhood_holdings.csv")
            temp_path.write_bytes(uploaded_holdings.getvalue())

            # Parse holdings
            current_holdings_df = parse_robinhood_holdings(str(temp_path))
            total_portfolio_value = current_holdings_df['current_value'].sum()

            st.success(f"✅ Loaded {len(current_holdings_df)} holdings | Total value: ${total_portfolio_value:,.2f}")

            # Show current holdings
            with st.expander("📊 View Current Holdings", expanded=True):
                display_holdings = current_holdings_df[['symbol', 'shares', 'current_price', 'current_value', 'current_weight']].copy()
                display_holdings.columns = ['Symbol', 'Shares', 'Current Price', 'Value ($)', 'Weight (%)']
                display_holdings['Weight (%)'] = (display_holdings['Weight (%)'] * 100).round(2)
                display_holdings['Value ($)'] = display_holdings['Value ($)'].round(2)
                display_holdings['Shares'] = display_holdings['Shares'].round(4)

                st.dataframe(display_holdings, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"❌ Error parsing holdings CSV: {e}")
            st.info("Make sure your CSV has columns for Symbol, Quantity/Shares, and Current Price")

    st.markdown("---")

    # Step 2: Select new portfolio
    st.subheader("📊 Step 2: Select New Portfolio")

    portfolio_source = st.radio(
        "Choose portfolio source:",
        ["📁 Load Saved Portfolio", "🆕 Generate New Portfolio"]
    )

    new_portfolio_df = None

    if portfolio_source == "📁 Load Saved Portfolio":
        # List available portfolios
        portfolio_dir = Path("results/portfolios")
        if portfolio_dir.exists():
            portfolio_files = sorted(
                portfolio_dir.glob("portfolio_*.csv"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if portfolio_files:
                # Show dropdown of portfolios
                portfolio_options = [f.name for f in portfolio_files[:10]]  # Show last 10
                selected_portfolio = st.selectbox(
                    "Select a portfolio:",
                    portfolio_options,
                    help="Showing the 10 most recent portfolios"
                )

                if selected_portfolio:
                    portfolio_path = portfolio_dir / selected_portfolio
                    new_portfolio_df = pd.read_csv(portfolio_path)

                    # Extract timestamp from filename
                    timestamp_match = selected_portfolio.replace("portfolio_", "").replace(".csv", "")
                    st.info(f"📅 Portfolio from: {timestamp_match}")

                    with st.expander("📊 View New Portfolio", expanded=False):
                        display_new = new_portfolio_df[['symbol', 'weight', 'momentum_return']].head(25).copy()
                        display_new.columns = ['Symbol', 'Weight', 'Momentum Return (%)']
                        display_new['Weight'] = (display_new['Weight'] * 100).round(2)
                        display_new['Momentum Return (%)'] = (display_new['Momentum Return (%)'] * 100).round(2)
                        st.dataframe(display_new, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ No saved portfolios found. Generate a portfolio first in '💼 Generate Portfolio' page.")
        else:
            st.warning("⚠️ No portfolios directory found. Generate a portfolio first.")

    else:  # Generate new portfolio
        st.info("💡 Switch to '💼 Generate Portfolio' page to create a new portfolio, then come back here.")
        st.markdown("Or generate a quick portfolio:")

        if st.button("🚀 Generate Portfolio Now (Default Settings)"):
            with st.spinner("Generating portfolio with default settings..."):
                try:
                    from scripts.generate_portfolio import generate_current_portfolio

                    portfolio_df = generate_current_portfolio(
                        use_llm=True,
                        portfolio_size=25,
                        enable_phase1=True,
                        enable_phase2=True,
                        enable_phase3=True,
                        enable_research_mode=False
                    )

                    if portfolio_df is not None and len(portfolio_df) > 0:
                        new_portfolio_df = portfolio_df
                        st.success(f"✅ Generated portfolio with {len(new_portfolio_df)} stocks")

                        with st.expander("📊 View Generated Portfolio", expanded=True):
                            display_new = new_portfolio_df[['symbol', 'weight', 'momentum_return']].head(25).copy()
                            display_new.columns = ['Symbol', 'Weight', 'Momentum Return (%)']
                            display_new['Weight'] = (display_new['Weight'] * 100).round(2)
                            display_new['Momentum Return (%)'] = (display_new['Momentum Return (%)'] * 100).round(2)
                            st.dataframe(display_new, use_container_width=True, hide_index=True)
                    else:
                        st.error("Failed to generate portfolio")

                except Exception as e:
                    st.error(f"Error generating portfolio: {e}")

    st.markdown("---")

    # Step 3: Calculate rebalancing
    if current_holdings_df is not None and new_portfolio_df is not None:
        st.subheader("🔄 Step 3: Calculate Rebalancing Trades")

        col1, col2 = st.columns(2)

        with col1:
            num_target_stocks = st.number_input(
                "Target number of stocks:",
                min_value=5,
                max_value=50,
                value=min(25, len(current_holdings_df)),
                help="How many stocks do you want in your rebalanced portfolio?"
            )

        with col2:
            rebalance_threshold = st.slider(
                "Rebalancing threshold (%):",
                min_value=1,
                max_value=20,
                value=5,
                help="Only rebalance positions where weight difference exceeds this threshold"
            ) / 100

        if st.button("🔄 Calculate Rebalancing Trades", type="primary"):
            with st.spinner("Calculating trades..."):
                try:
                    from src.utils.robinhood_export import calculate_rebalancing_trades, generate_rebalancing_instructions

                    trades_df, summary = calculate_rebalancing_trades(
                        current_holdings=current_holdings_df,
                        new_portfolio=new_portfolio_df,
                        total_portfolio_value=total_portfolio_value,
                        num_stocks=num_target_stocks,
                        rebalance_threshold=rebalance_threshold
                    )

                    # Store in session state
                    st.session_state.rebalancing_trades = trades_df
                    st.session_state.rebalancing_summary = summary

                    st.success("✅ Rebalancing calculated successfully!")

                except Exception as e:
                    st.error(f"❌ Error calculating rebalancing: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        # Display results if available
        if 'rebalancing_trades' in st.session_state and 'rebalancing_summary' in st.session_state:
            st.markdown("---")
            st.subheader("📋 Rebalancing Summary")

            summary = st.session_state.rebalancing_summary
            trades_df = st.session_state.rebalancing_trades

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Portfolio Value", f"${summary['total_portfolio_value']:,.0f}")

            with col2:
                st.metric("Stocks to Sell", summary['num_stocks_to_sell'])

            with col3:
                st.metric("Stocks to Buy", summary['num_stocks_to_buy'])

            with col4:
                st.metric("Turnover Rate", f"{summary['turnover_rate']*100:.1f}%")

            st.markdown("---")

            # Show trades table
            if len(trades_df) > 0:
                st.subheader("📊 Trades to Execute")

                # Format for display
                display_trades = trades_df.copy()

                # Round numeric columns
                for col in display_trades.columns:
                    if col.endswith('_$'):
                        display_trades[col] = display_trades[col].round(2)
                    elif col.endswith('_%'):
                        display_trades[col] = display_trades[col].round(2)

                # Color-code actions
                def highlight_action(row):
                    if row['Action'] == 'SELL':
                        return ['background-color: #ffcccc'] * len(row)
                    elif row['Action'] == 'BUY':
                        return ['background-color: #ccffcc'] * len(row)
                    elif 'Reduce' in row['Action']:
                        return ['background-color: #ffe6cc'] * len(row)
                    elif 'Add' in row['Action']:
                        return ['background-color: #cce6ff'] * len(row)
                    return [''] * len(row)

                st.dataframe(
                    display_trades.style.apply(highlight_action, axis=1),
                    use_container_width=True,
                    hide_index=True
                )

                # Legend
                st.markdown("""
                **Legend:**
                - 🔴 Red = SELL (eliminate position)
                - 🟢 Green = BUY (new position)
                - 🟠 Orange = REDUCE (partial sell)
                - 🔵 Blue = ADD (partial buy)
                """)

                st.markdown("---")

                # Generate instructions
                st.subheader("📖 Trading Instructions")

                instructions = generate_rebalancing_instructions(
                    trades_df=trades_df,
                    summary=summary,
                    excluded_stocks=[]
                )

                # Show instructions
                with st.expander("📖 View Full Instructions", expanded=True):
                    st.code(instructions, language="")

                # Download buttons
                col1, col2 = st.columns(2)

                with col1:
                    # Download trades CSV
                    csv_data = trades_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Trades CSV",
                        data=csv_data,
                        file_name=f"rebalancing_trades_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

                with col2:
                    # Download instructions
                    st.download_button(
                        label="📥 Download Instructions",
                        data=instructions,
                        file_name=f"rebalancing_instructions_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )

            else:
                st.info("✅ No trades needed! Your portfolio is already well-balanced.")

    elif current_holdings_df is None:
        st.info("👆 Upload your current holdings to get started")
    elif new_portfolio_df is None:
        st.info("👆 Select or generate a new portfolio to compare")

# ============================================================
# PAGE 4: ANALYZE INDIVIDUAL STOCK
# ============================================================
elif page == "🔍 Analyze Individual Stock":
    st.markdown('<p class="main-header">Analyze Individual Stock</p>', unsafe_allow_html=True)
    st.markdown("Get AI-powered sentiment and risk analysis for any stock")

    st.markdown("---")

    # Input section
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("📊 Stock Selection")
        ticker = st.text_input("Enter Stock Ticker", value="AAPL", max_chars=10).upper()

        st.markdown("---")
        st.subheader("⚙️ Analysis Options")

        run_llm = st.checkbox("🤖 Run LLM Sentiment Analysis", value=True)
        run_risk = st.checkbox("🔍 Run Risk Assessment", value=True)
        use_research_mode = st.checkbox(
            "🔬 Use Research Mode",
            value=False,
            help="Get detailed AI analysis (3-5 sentences) instead of just a score"
        )
        store_prompts = st.checkbox("📝 Store Prompts (view what AI analyzed)", value=True)

        if run_llm or run_risk:
            model = st.selectbox(
                "LLM Model",
                ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                index=0,
                help="gpt-4o-mini is fastest and cheapest"
            )
        else:
            model = None

        analyze_button = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)

    with col2:
        st.subheader("ℹ️ What This Does")
        st.markdown("""
        This tool analyzes any stock using the same AI that powers the portfolio generator:

        **📈 Momentum Analysis:**
        - Calculates 12-month return
        - Shows how stock compares to SP500

        **🤖 LLM Sentiment (optional):**
        - Analyzes recent news (last 3-7 days)
        - Predicts momentum continuation probability
        - Score: 0.0 = bearish, 1.0 = very bullish

        **🔍 Risk Assessment (optional):**
        - Evaluates 5 risk categories from news
        - Identifies company-specific concerns
        - Score: 0.0 = very safe, 1.0 = very risky

        **📝 Prompt Viewing:**
        - See exactly what news was analyzed
        - View the prompts sent to AI
        - Verify and validate all decisions
        """)

    # Analysis section
    if analyze_button:
        if not ticker:
            st.error("Please enter a stock ticker")
        else:
            with st.spinner(f"Analyzing {ticker}..."):
                try:
                    from src.data import DataManager
                    from src.strategy import StockSelector
                    from src.llm import LLMScorer, LLMRiskScorer, get_prompt_store

                    dm = DataManager()

                    # Initialize prompt store if needed
                    prompt_store = None
                    if store_prompts:
                        prompt_store = get_prompt_store()
                        prompt_store.clear_session()

                    # Fetch price data
                    st.info(f"📊 Fetching price data for {ticker}...")
                    price_data = dm.get_prices([ticker], use_cache=True, show_progress=False)

                    if ticker not in price_data or price_data[ticker].empty:
                        st.error(f"❌ Could not fetch data for {ticker}. Please check the ticker symbol.")
                    else:
                        prices = price_data[ticker]

                        # Calculate momentum (simple 12-month return)
                        if 'adjusted_close' in prices.columns and len(prices) >= 252:
                            # Get price from 252 trading days ago (12 months)
                            start_price = prices['adjusted_close'].iloc[-252]
                            end_price = prices['adjusted_close'].iloc[-1]
                            momentum_return = (end_price / start_price) - 1
                        else:
                            momentum_return = None

                        # Get SPY for comparison
                        spy_data = dm.get_prices(['SPY'], use_cache=True, show_progress=False)
                        if 'SPY' in spy_data and not spy_data['SPY'].empty:
                            spy_prices = spy_data['SPY']
                            if 'adjusted_close' in spy_prices.columns and len(spy_prices) >= 252:
                                spy_start = spy_prices['adjusted_close'].iloc[-252]
                                spy_end = spy_prices['adjusted_close'].iloc[-1]
                                spy_momentum = (spy_end / spy_start) - 1
                            else:
                                spy_momentum = None
                        else:
                            spy_momentum = None

                        # Fetch news
                        news_data = dm.get_news([ticker], lookback_days=5, use_cache=True)
                        news_articles = news_data.get(ticker, [])

                        # Display results
                        st.markdown("---")
                        st.subheader(f"📊 Analysis Results for {ticker}")

                        # Basic metrics
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if momentum_return is not None:
                                st.metric("12-Month Momentum", f"{momentum_return*100:.2f}%")
                            else:
                                st.metric("12-Month Momentum", "N/A")
                                st.caption("Insufficient price history")

                        with col2:
                            if momentum_return is not None and spy_momentum is not None:
                                relative_perf = (momentum_return - spy_momentum) * 100
                                st.metric("vs SPY", f"{relative_perf:+.2f}%",
                                         delta_color="normal" if relative_perf > 0 else "inverse")
                            else:
                                st.metric("vs SPY", "N/A")

                        with col3:
                            st.metric("News Articles", len(news_articles))

                        # News preview
                        st.markdown("---")
                        st.subheader("📰 Recent News (Last 5 Days)")

                        if news_articles:
                            with st.expander(f"View {len(news_articles)} news articles", expanded=False):
                                for i, article in enumerate(news_articles[:10], 1):
                                    st.markdown(f"**{i}.** {article[:200]}..." if len(article) > 200 else f"**{i}.** {article}")
                                if len(news_articles) > 10:
                                    st.caption(f"... and {len(news_articles)-10} more articles")
                        else:
                            st.info("No recent news found for this stock")

                        # Earnings Data
                        st.markdown("---")
                        st.subheader("📊 Earnings & Fundamentals")

                        # Fetch earnings data (will be used by LLM too)
                        earnings_data = None
                        with st.spinner("Fetching earnings data..."):
                            try:
                                earnings_data = dm.get_earnings_for_symbol(ticker, use_cache=True)

                                if earnings_data:
                                    # Show key metrics
                                    col1, col2, col3, col4 = st.columns(4)

                                    with col1:
                                        if earnings_data.get('latest_eps') is not None:
                                            st.metric("Latest EPS", f"${earnings_data['latest_eps']:.2f}")
                                        else:
                                            st.metric("Latest EPS", "N/A")

                                    with col2:
                                        if earnings_data.get('yoy_eps_growth') is not None:
                                            yoy_eps = earnings_data['yoy_eps_growth']
                                            st.metric("YoY EPS Growth", f"{yoy_eps*100:+.1f}%",
                                                     delta_color="normal" if yoy_eps > 0 else "inverse")
                                        else:
                                            st.metric("YoY EPS Growth", "N/A")

                                    with col3:
                                        if earnings_data.get('profit_margin') is not None:
                                            st.metric("Profit Margin", f"{earnings_data['profit_margin']*100:.1f}%")
                                        else:
                                            st.metric("Profit Margin", "N/A")

                                    with col4:
                                        if earnings_data.get('debt_to_equity') is not None:
                                            st.metric("Debt/Equity", f"{earnings_data['debt_to_equity']:.2f}")
                                        else:
                                            st.metric("Debt/Equity", "N/A")

                                    # Detailed earnings view
                                    with st.expander("📈 View Full Earnings Details", expanded=False):
                                        st.markdown(f"**Quarter:** {earnings_data.get('latest_quarter_date', 'N/A')}")

                                        if earnings_data.get('latest_revenue'):
                                            st.markdown(f"**Revenue:** ${earnings_data['latest_revenue']:,.0f}")

                                        if earnings_data.get('yoy_revenue_growth') is not None:
                                            st.markdown(f"**YoY Revenue Growth:** {earnings_data['yoy_revenue_growth']*100:+.1f}%")

                                        if earnings_data.get('operating_margin') is not None:
                                            st.markdown(f"**Operating Margin:** {earnings_data['operating_margin']*100:.1f}%")

                                        if earnings_data.get('gross_margin') is not None:
                                            st.markdown(f"**Gross Margin:** {earnings_data['gross_margin']*100:.1f}%")

                                        if earnings_data.get('roe') is not None:
                                            st.markdown(f"**ROE:** {earnings_data['roe']*100:.1f}%")

                                        if earnings_data.get('roa') is not None:
                                            st.markdown(f"**ROA:** {earnings_data['roa']*100:.1f}%")
                                else:
                                    st.info("No earnings data available for this stock")

                            except Exception as e:
                                st.warning(f"Could not fetch earnings data: {e}")

                        # Analyst Ratings & Targets (Phase 3)
                        st.markdown("---")
                        st.subheader("🎯 Analyst Ratings & Price Targets")

                        # Fetch analyst data (will be used by LLM too)
                        analyst_data = None
                        with st.spinner("Fetching analyst ratings..."):
                            try:
                                analyst_data = dm.get_analyst_data_for_symbol(ticker, use_cache=True)

                                if analyst_data:
                                    # Show key metrics
                                    col1, col2, col3, col4 = st.columns(4)

                                    with col1:
                                        rec = analyst_data.get('recommendation', 'N/A')
                                        rec_mean = analyst_data.get('recommendation_mean')
                                        if rec_mean:
                                            if rec_mean <= 1.5:
                                                st.success(f"**{rec.upper()}** 🟢")
                                            elif rec_mean <= 2.5:
                                                st.info(f"**{rec.upper()}** 🟡")
                                            elif rec_mean <= 3.5:
                                                st.warning(f"**{rec.upper()}** 🟠")
                                            else:
                                                st.error(f"**{rec.upper()}** 🔴")
                                        else:
                                            st.metric("Consensus", rec)

                                    with col2:
                                        num_analysts = analyst_data.get('number_of_analysts')
                                        if num_analysts:
                                            st.metric("# Analysts", f"{num_analysts}")
                                        else:
                                            st.metric("# Analysts", "N/A")

                                    with col3:
                                        target_mean = analyst_data.get('target_mean_price')
                                        if target_mean:
                                            st.metric("Price Target", f"${target_mean:.2f}")
                                        else:
                                            st.metric("Price Target", "N/A")

                                    with col4:
                                        upside = analyst_data.get('upside_potential')
                                        if upside is not None:
                                            st.metric("Upside", f"{upside*100:+.1f}%",
                                                     delta_color="normal" if upside > 0 else "inverse")
                                        else:
                                            st.metric("Upside", "N/A")

                                    # Detailed analyst view
                                    with st.expander("📊 View Full Analyst Details", expanded=False):
                                        if analyst_data.get('target_high_price') and analyst_data.get('target_low_price'):
                                            st.markdown(f"**Price Target Range:** ${analyst_data['target_low_price']:.2f} - ${analyst_data['target_high_price']:.2f}")

                                        if analyst_data.get('current_price'):
                                            st.markdown(f"**Current Price:** ${analyst_data['current_price']:.2f}")

                                        if analyst_data.get('forward_eps'):
                                            st.markdown(f"**Forward EPS:** ${analyst_data['forward_eps']:.2f}")

                                        if analyst_data.get('forward_pe'):
                                            st.markdown(f"**Forward P/E:** {analyst_data['forward_pe']:.1f}x")

                                        if analyst_data.get('earnings_growth') is not None:
                                            st.markdown(f"**Earnings Growth Estimate:** {analyst_data['earnings_growth']*100:+.1f}%")

                                        if analyst_data.get('revenue_growth') is not None:
                                            st.markdown(f"**Revenue Growth Estimate:** {analyst_data['revenue_growth']*100:+.1f}%")

                                        # Recent upgrades/downgrades
                                        upgrades = analyst_data.get('recent_upgrades')
                                        downgrades = analyst_data.get('recent_downgrades')
                                        if upgrades is not None and downgrades is not None:
                                            st.markdown(f"**Recent Changes (90 days):**")
                                            st.markdown(f"  - Upgrades: {upgrades}")
                                            st.markdown(f"  - Downgrades: {downgrades}")
                                            if upgrades > downgrades:
                                                st.markdown(f"  - Trend: 🟢 Positive ({upgrades - downgrades} net upgrades)")
                                            elif downgrades > upgrades:
                                                st.markdown(f"  - Trend: 🔴 Negative ({downgrades - upgrades} net downgrades)")
                                            else:
                                                st.markdown(f"  - Trend: ⚪ Neutral")
                                else:
                                    st.info("No analyst data available for this stock")

                            except Exception as e:
                                st.warning(f"Could not fetch analyst data: {e}")

                        # LLM Sentiment Analysis
                        if run_llm:
                            st.markdown("---")
                            st.subheader("🤖 LLM Sentiment Analysis")

                            with st.spinner("Running AI sentiment analysis..."):
                                try:
                                    scorer = LLMScorer(model=model)

                                    # Get news summary
                                    from src.llm.prompts import PromptTemplate
                                    news_summary = PromptTemplate.format_news_for_prompt(
                                        news_articles,
                                        max_articles=20,
                                        max_chars=3000,
                                        prioritize_important=True
                                    )

                                    # Score with prompt return (including earnings and analyst data)
                                    # Use research mode if enabled
                                    if use_research_mode:
                                        result = scorer.score_stock_with_research(
                                            symbol=ticker,
                                            news_summary=news_summary,
                                            momentum_return=momentum_return,
                                            earnings_data=earnings_data,
                                            analyst_data=analyst_data,
                                            return_prompt=store_prompts
                                        )

                                        if store_prompts and len(result) == 4:
                                            raw_score, normalized_score, analysis, prompt = result
                                        else:
                                            raw_score, normalized_score, analysis = result
                                            prompt = None
                                    else:
                                        result = scorer.score_stock(
                                            symbol=ticker,
                                            news_summary=news_summary,
                                            momentum_return=momentum_return,
                                            earnings_data=earnings_data,
                                            analyst_data=analyst_data,
                                            return_prompt=store_prompts
                                        )

                                        if store_prompts and len(result) == 3:
                                            raw_score, normalized_score, prompt = result
                                        else:
                                            raw_score, normalized_score = result
                                            prompt = None
                                        analysis = None

                                    # Store prompt
                                    if store_prompts and prompt_store and prompt:
                                        prompt_store.store_prompt(
                                            symbol=ticker,
                                            prompt=prompt,
                                            prompt_type='llm_scoring',
                                            metadata={'score': normalized_score, 'model': model}
                                        )

                                    # Display score
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        if normalized_score >= 0.7:
                                            st.success(f"**Score: {normalized_score:.3f}** 🟢 Bullish")
                                        elif normalized_score >= 0.5:
                                            st.info(f"**Score: {normalized_score:.3f}** 🟡 Neutral")
                                        else:
                                            st.warning(f"**Score: {normalized_score:.3f}** 🔴 Cautious")

                                        st.caption("0.0 = bearish, 0.5 = neutral, 1.0 = very bullish")

                                    with col2:
                                        if normalized_score >= 0.9:
                                            interpretation = "Very Bullish - News strongly suggests momentum will continue"
                                        elif normalized_score >= 0.7:
                                            interpretation = "Bullish - News indicates likely momentum continuation"
                                        elif normalized_score >= 0.5:
                                            interpretation = "Neutral - Mixed signals in recent news"
                                        elif normalized_score >= 0.3:
                                            interpretation = "Cautious - News suggests potential momentum slowdown"
                                        else:
                                            interpretation = "Bearish - News indicates momentum may not continue"

                                        st.markdown(f"**Interpretation:** {interpretation}")

                                    # Show AI analysis if research mode was used
                                    if use_research_mode and analysis:
                                        st.markdown("---")
                                        st.markdown("### 🔬 AI Analysis (Research Mode)")
                                        st.info(analysis)
                                        st.caption("💡 This detailed analysis was generated using research mode")

                                    # Show prompt if stored
                                    if store_prompts and prompt:
                                        with st.expander("📝 View LLM Prompt (what was sent to AI)", expanded=False):
                                            st.markdown("**This is exactly what was sent to the AI for analysis:**")
                                            st.code(prompt, language="text")
                                            st.caption(f"Prompt length: {len(prompt)} characters")

                                except Exception as e:
                                    st.error(f"Error during LLM analysis: {e}")
                                    import traceback
                                    with st.expander("View error details"):
                                        st.code(traceback.format_exc())

                        # Risk Assessment
                        if run_risk:
                            st.markdown("---")
                            st.subheader("🔍 Risk Assessment")

                            with st.spinner("Running risk analysis..."):
                                try:
                                    risk_scorer = LLMRiskScorer(model=model)

                                    # Score with prompt return
                                    risk_result = risk_scorer.score_stock_risk(
                                        symbol=ticker,
                                        news_articles=news_articles,
                                        max_articles=10,
                                        return_prompt=store_prompts
                                    )

                                    # Store prompt
                                    if store_prompts and prompt_store and 'risk_prompt' in risk_result:
                                        prompt_store.store_prompt(
                                            symbol=ticker,
                                            prompt=risk_result['risk_prompt'],
                                            prompt_type='risk_scoring',
                                            metadata={'risk_score': risk_result['overall_risk_score'], 'model': model}
                                        )

                                    # Display risk score
                                    risk_score = risk_result['overall_risk_score']
                                    key_risk = risk_result.get('key_risk', 'None identified')

                                    col1, col2 = st.columns(2)

                                    with col1:
                                        if risk_score < 0.4:
                                            st.success(f"**Risk Score: {risk_score:.2f}** 🟢 Low Risk")
                                        elif risk_score < 0.7:
                                            st.warning(f"**Risk Score: {risk_score:.2f}** 🟡 Medium Risk")
                                        else:
                                            st.error(f"**Risk Score: {risk_score:.2f}** 🔴 High Risk")

                                        st.caption("0.0 = very safe, 1.0 = very risky")

                                    with col2:
                                        st.markdown(f"**Key Risk:** {key_risk}")
                                        st.markdown(f"**Recommendation:** {risk_result.get('recommendation', 'N/A')}")

                                    # Risk category breakdown
                                    st.markdown("**Risk Category Breakdown:**")

                                    risk_categories = {
                                        'financial_risk': ('💰', 'Financial', 'earnings, debt, cash flow'),
                                        'operational_risk': ('⚙️', 'Operational', 'supply chain, production'),
                                        'regulatory_risk': ('⚖️', 'Regulatory', 'legal, compliance'),
                                        'competitive_risk': ('🏁', 'Competitive', 'market share, rivals'),
                                        'market_risk': ('📊', 'Market', 'sector trends, macro')
                                    }

                                    cols = st.columns(5)
                                    for idx, (risk_type, (emoji, name, desc)) in enumerate(risk_categories.items()):
                                        if risk_type in risk_result:
                                            level = risk_result[risk_type]
                                            if level == "LOW":
                                                indicator = "🟢"
                                            elif level == "MEDIUM":
                                                indicator = "🟡"
                                            else:
                                                indicator = "🔴"

                                            with cols[idx]:
                                                st.markdown(f"{emoji} **{name}**")
                                                st.markdown(f"{indicator} {level}")
                                                st.caption(desc)

                                    # Show prompt if stored
                                    if store_prompts and 'risk_prompt' in risk_result:
                                        with st.expander("🔍 View Risk Prompt (what was sent to AI)", expanded=False):
                                            st.markdown("**This is exactly what was sent to the AI for risk analysis:**")
                                            st.code(risk_result['risk_prompt'], language="text")
                                            st.caption(f"Prompt length: {len(risk_result['risk_prompt'])} characters")

                                except Exception as e:
                                    st.error(f"Error during risk analysis: {e}")
                                    import traceback
                                    with st.expander("View error details"):
                                        st.code(traceback.format_exc())

                        # Summary
                        st.markdown("---")
                        st.success("✅ Analysis complete!")

                        if run_llm and run_risk:
                            st.info("💡 **Tip:** You can now use this stock in your portfolio decisions with confidence in the AI analysis.")
                        elif run_llm:
                            st.info("💡 **Tip:** Enable Risk Assessment for a complete picture of company-specific risks.")
                        elif run_risk:
                            st.info("💡 **Tip:** Enable LLM Sentiment to understand momentum continuation probability.")

                except Exception as e:
                    st.error(f"❌ Error analyzing {ticker}: {e}")
                    import traceback
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())

# ============================================================
# PAGE 4: ROBINHOOD ORDERS
# ============================================================
elif page == "🎯 Robinhood Orders":
    st.markdown('<p class="main-header">Generate Robinhood Order List</p>', unsafe_allow_html=True)
    st.markdown("Convert your portfolio into step-by-step Robinhood trades")

    st.markdown("---")

    # Instructions
    with st.expander("📖 How to Use", expanded=False):
        st.markdown("""
        **Month 1 (Initial Investment)**:
        1. Generate portfolio in "Generate Portfolio" tab
        2. Enter your capital (e.g., $10,000)
        3. Click "Generate Order List"
        4. Download CSV and execute on Robinhood
        5. Save the generated portfolio as "Current Holdings" for next month

        **Month 2+ (Rebalancing)**:
        1. Generate new portfolio in "Generate Portfolio" tab
        2. Upload your saved holdings from last month
        3. Enter current portfolio value (check Robinhood)
        4. Click "Generate Order List" - **only the changes will show!**
        5. Execute only the SELL and BUY orders (skip rebalancing if weights are close)

        **Expected turnover**: 10-30% per month (only 2-4 stocks change typically)
        """)

    st.markdown("---")

    # Input section
    st.subheader("📋 Order Generation Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**1️⃣ Select Portfolio**")

        # Get list of generated portfolios
        portfolio_dir = Path("results/portfolios")
        if portfolio_dir.exists():
            portfolio_files = sorted(portfolio_dir.glob("*.csv"), reverse=True)

            if portfolio_files:
                # Use session state portfolio if available
                if 'portfolio_df' in st.session_state and st.session_state.portfolio_df is not None:
                    st.info("✅ Using portfolio from 'Generate Portfolio' tab")
                    selected_portfolio = "current_session"
                else:
                    # Show dropdown of saved portfolios
                    portfolio_options = [f.name for f in portfolio_files[:10]]  # Show last 10
                    selected_file = st.selectbox(
                        "Choose portfolio file:",
                        options=portfolio_options,
                        help="Select a portfolio CSV generated from 'Generate Portfolio' tab"
                    )
                    selected_portfolio = portfolio_dir / selected_file
            else:
                st.warning("⚠️ No portfolios found. Generate one in 'Generate Portfolio' tab first.")
                selected_portfolio = None
        else:
            st.warning("⚠️ No portfolios found. Generate one in 'Generate Portfolio' tab first.")
            selected_portfolio = None

        st.markdown("**2️⃣ Enter Capital**")

        # Auto-populate from Robinhood if available
        default_capital = 10000.0
        if 'rh_fetcher' in st.session_state and st.session_state.rh_fetcher.logged_in:
            try:
                rh_total_value = st.session_state.rh_fetcher.get_portfolio_value()
                default_capital = rh_total_value
                st.info(f"✨ Auto-filled from Robinhood: ${rh_total_value:,.2f}")
            except:
                pass

        capital = st.number_input(
            "Total Portfolio Value ($)",
            min_value=100.0,
            max_value=10000000.0,
            value=default_capital,
            step=100.0,
            help="Your current Robinhood account balance (+ any new deposits)"
        )

        st.markdown("💡 **How to determine capital**:")
        st.markdown("""
        - **Month 1**: Your initial investment (e.g., $10,000)
        - **Month 2+**: Current Robinhood balance (check app)
        - **Adding money**: Current balance + new deposit
        """)

    with col2:
        st.markdown("**3️⃣ Get Current Holdings (Optional)**")
        st.markdown("*Skip this for Month 1 (initial investment)*")

        # Robinhood API integration is disabled (not implemented)
        # Use the manual CSV export feature in "Generate Portfolio" page instead
        if 'rh_holdings' not in st.session_state:
            st.session_state.rh_holdings = None

        holdings_method = st.radio(
            "Choose method:",
            ["📁 Upload CSV (Manual)"],  # API option removed - use export feature in Generate Portfolio page
            help="Upload your current holdings CSV exported from Robinhood"
        )

        if holdings_method == "🔗 Connect to Robinhood API (Automatic)" and False:  # DISABLED
            # Robinhood API login
            if not st.session_state.rh_fetcher.logged_in:
                st.markdown("**Robinhood Login**")

                with st.form("rh_login_form"):
                    rh_username = st.text_input("Email/Username", type="default")
                    rh_password = st.text_input("Password", type="password")
                    rh_mfa = st.text_input("2FA Code (if enabled)", help="6-digit code from authenticator app")

                    submit = st.form_submit_button("🔐 Connect to Robinhood")

                    if submit:
                        if not rh_username or not rh_password:
                            st.error("Please enter username and password")
                        else:
                            with st.spinner("Connecting to Robinhood..."):
                                success, message = st.session_state.rh_fetcher.login(
                                    rh_username,
                                    rh_password,
                                    rh_mfa if rh_mfa else None
                                )

                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

                st.info("🔒 **Security**: Credentials are not saved. Connection is read-only (no trades executed).")
            else:
                st.success(f"✅ Connected to Robinhood as {st.session_state.rh_fetcher.username}")

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("📥 Fetch Current Holdings"):
                        with st.spinner("Fetching positions from Robinhood..."):
                            try:
                                holdings_df = st.session_state.rh_fetcher.get_current_positions()
                                st.session_state.rh_holdings = holdings_df

                                total_value = st.session_state.rh_fetcher.get_portfolio_value()
                                st.success(f"✅ Fetched {len(holdings_df)} positions (${total_value:,.2f} total)")

                            except Exception as e:
                                st.error(f"Error fetching holdings: {e}")

                with col_b:
                    if st.button("🚪 Disconnect"):
                        st.session_state.rh_fetcher.logout()
                        st.session_state.rh_holdings = None
                        st.rerun()

                # Show fetched holdings
                if st.session_state.rh_holdings is not None and not st.session_state.rh_holdings.empty:
                    with st.expander("👀 View Current Holdings", expanded=False):
                        display_df = st.session_state.rh_holdings[['symbol', 'shares', 'current_price', 'market_value', 'weight']].copy()
                        display_df['weight'] = display_df['weight'].apply(lambda x: f"{x*100:.2f}%")
                        display_df['market_value'] = display_df['market_value'].apply(lambda x: f"${x:,.2f}")
                        display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
                        st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Set holdings for processing
            current_holdings_df = st.session_state.rh_holdings if st.session_state.rh_holdings is not None else None
            current_holdings_file = None  # Not using file for API method

        else:  # Manual CSV upload
            uploaded_file = st.file_uploader(
                "Upload CSV with current holdings",
                type=['csv'],
                help="Upload your portfolio from last month to see only the changes"
            )

            if uploaded_file is not None:
                try:
                    current_holdings_df = pd.read_csv(uploaded_file)
                    st.success(f"✅ Loaded {len(current_holdings_df)} current positions")

                    # Save to temp file
                    temp_holdings_path = Path("temp_current_holdings.csv")
                    current_holdings_df.to_csv(temp_holdings_path, index=False)
                    current_holdings_file = str(temp_holdings_path)
                except Exception as e:
                    st.error(f"Error loading file: {e}")
                    current_holdings_df = None
                    current_holdings_file = None
            else:
                current_holdings_df = None
                current_holdings_file = None
                st.info("ℹ️ No current holdings uploaded - will show all positions as new buys")

    st.markdown("---")

    # Generate button
    if st.button("🎯 Generate Robinhood Order List", type="primary", use_container_width=True):
        if selected_portfolio is None:
            st.error("❌ Please generate a portfolio first in 'Generate Portfolio' tab")
        else:
            with st.spinner("Generating order list..."):
                try:
                    # Load portfolio
                    if selected_portfolio == "current_session":
                        portfolio_df = st.session_state.portfolio_df
                        # Save to temp file for processing
                        temp_portfolio_path = Path("temp_generated_portfolio.csv")
                        portfolio_df.to_csv(temp_portfolio_path, index=False)
                        portfolio_file = str(temp_portfolio_path)
                    else:
                        portfolio_file = str(selected_portfolio)
                        portfolio_df = pd.read_csv(portfolio_file)

                    # Calculate position values
                    portfolio_df['position_value'] = portfolio_df['weight'] * capital
                    portfolio_df['position_value'] = portfolio_df['position_value'].round(2)

                    # Load current holdings if provided
                    if current_holdings_df is not None and not current_holdings_df.empty:
                        # Use DataFrame directly (from Robinhood API or CSV)
                        current_symbols = set(current_holdings_df['symbol'].values)
                        current_holdings_for_display = current_holdings_df
                    elif current_holdings_file:
                        # Fallback to file path
                        current_df = pd.read_csv(current_holdings_file)
                        current_symbols = set(current_df['symbol'].values)
                        current_holdings_for_display = current_df
                    else:
                        current_symbols = set()
                        current_holdings_for_display = None

                    new_symbols = set(portfolio_df['symbol'].values)

                    # Categorize trades
                    sells = current_symbols - new_symbols
                    buys = new_symbols - current_symbols
                    holds = current_symbols & new_symbols

                    # Store in session state
                    st.session_state.order_data = {
                        'portfolio_df': portfolio_df,
                        'capital': capital,
                        'sells': sells,
                        'buys': buys,
                        'holds': holds,
                        'current_symbols': current_symbols,
                        'current_holdings': current_holdings_for_display
                    }

                    st.success("✅ Order list generated successfully!")

                except Exception as e:
                    st.error(f"❌ Error generating orders: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    # Display results
    if 'order_data' in st.session_state:
        data = st.session_state.order_data
        portfolio_df = data['portfolio_df']
        capital = data['capital']
        sells = data['sells']
        buys = data['buys']
        holds = data['holds']
        current_symbols = data['current_symbols']

        st.markdown("---")
        st.subheader("📋 STEP-BY-STEP ROBINHOOD ORDERS")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Positions", len(portfolio_df))
        with col2:
            st.metric("Sells", len(sells))
        with col3:
            st.metric("Buys", len(buys))
        with col4:
            turnover = (len(sells) + len(buys)) / max(len(current_symbols), 1) if current_symbols else 1.0
            st.metric("Turnover", f"{turnover*100:.1f}%")

        st.markdown("---")

        # STEP 1: SELLS
        st.markdown("### STEP 1: SELL ORDERS (Exit Positions)")
        if sells:
            st.markdown(f"*Sell these {len(sells)} positions completely*")
            sell_data = []
            for i, symbol in enumerate(sorted(sells), 1):
                sell_data.append({
                    'Step': f'1.{i}',
                    'Action': 'SELL',
                    'Symbol': symbol,
                    'Amount': 'ALL',
                    'Instructions': 'Sell 100% of position'
                })
            st.dataframe(pd.DataFrame(sell_data), use_container_width=True, hide_index=True)
        else:
            st.info("✅ No sells needed")

        st.markdown("---")

        # STEP 2: BUYS
        st.markdown("### STEP 2: BUY NEW POSITIONS")
        if buys:
            st.markdown(f"*Buy these {len(buys)} new stocks*")
            buy_data = []
            for i, symbol in enumerate(sorted(buys), 1):
                row = portfolio_df[portfolio_df['symbol'] == symbol].iloc[0]
                amount = row['position_value']
                weight = row['weight'] * 100
                buy_data.append({
                    'Step': f'2.{i}',
                    'Action': 'BUY',
                    'Symbol': symbol,
                    'Amount': f'${amount:.2f}',
                    'Weight': f'{weight:.2f}%',
                    'Instructions': f'Buy ${amount:.2f} worth (use "Dollars" not "Shares")'
                })
            st.dataframe(pd.DataFrame(buy_data), use_container_width=True, hide_index=True)
        else:
            st.info("✅ No new buys needed")

        st.markdown("---")

        # STEP 3: REBALANCE (Optional)
        st.markdown("### STEP 3: REBALANCE EXISTING POSITIONS (Optional)")
        if holds:
            st.markdown(f"*Adjust these {len(holds)} positions if weights drifted significantly (>2%)*")
            st.markdown("💡 **Tip**: You can skip this step if you're okay with slight weight differences")

            # Check if we have current holdings data (from Robinhood API)
            current_holdings = data.get('current_holdings')
            has_current_data = current_holdings is not None and not current_holdings.empty

            rebalance_data = []
            for i, symbol in enumerate(sorted(holds), 1):
                row = portfolio_df[portfolio_df['symbol'] == symbol].iloc[0]
                target_value = row['position_value']
                target_weight = row['weight'] * 100

                rebal_row = {
                    'Step': f'3.{i}',
                    'Symbol': symbol,
                    'Target Value': f'${target_value:.2f}',
                    'Target Weight': f'{target_weight:.2f}%'
                }

                # Add current values if available
                if has_current_data and symbol in current_holdings['symbol'].values:
                    current_row = current_holdings[current_holdings['symbol'] == symbol].iloc[0]
                    current_value = current_row.get('market_value', 0)
                    current_weight = current_row.get('weight', 0) * 100
                    diff_value = target_value - current_value

                    rebal_row['Current Value'] = f'${current_value:.2f}'
                    rebal_row['Current Weight'] = f'{current_weight:.2f}%'
                    rebal_row['Difference'] = f'${diff_value:+.2f}'

                    # Only show action if difference > $50 or weight diff > 2%
                    if abs(diff_value) > 50 or abs(target_weight - current_weight) > 2:
                        if diff_value > 0:
                            rebal_row['Action'] = f'BUY ${abs(diff_value):.2f}'
                        else:
                            rebal_row['Action'] = f'SELL ${abs(diff_value):.2f}'
                    else:
                        rebal_row['Action'] = 'HOLD (close enough)'
                else:
                    rebal_row['Instructions'] = 'Check current value, buy/sell to reach target'

                rebalance_data.append(rebal_row)

            st.dataframe(pd.DataFrame(rebalance_data), use_container_width=True, hide_index=True)

            if has_current_data:
                st.success("✨ **Live data from Robinhood**: Showing exact current vs target values!")
        else:
            st.info("✅ No rebalancing needed")

        st.markdown("---")

        # Execution instructions
        st.markdown("### 📱 HOW TO EXECUTE ON ROBINHOOD")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **For SELL orders:**
            1. Search for stock symbol
            2. Click "Trade" → "Sell"
            3. Select "Dollars" (not shares)
            4. Click "Max" to sell all
            5. Choose "Market Order"
            6. Review and submit
            """)

        with col2:
            st.markdown("""
            **For BUY orders:**
            1. Search for stock symbol
            2. Click "Trade" → "Buy"
            3. Select "Dollars" (not shares)
            4. Enter exact dollar amount from list
            5. Choose "Market Order"
            6. Review and submit
            """)

        st.info("⏰ **Best time to trade**: 10:00 AM - 3:00 PM ET (avoid first/last 30 minutes)")
        st.success("💰 **Cost**: $0 (Robinhood is commission-free)")

        # Download CSV
        st.markdown("---")
        st.markdown("### 💾 Download Order List")

        # Create downloadable CSV
        all_orders = []

        # Add sells
        for i, symbol in enumerate(sorted(sells), 1):
            all_orders.append({
                'step': f'1.{i}',
                'action': 'SELL',
                'symbol': symbol,
                'amount': 'ALL',
                'notes': 'Sell 100% of position'
            })

        # Add buys
        for i, symbol in enumerate(sorted(buys), 1):
            row = portfolio_df[portfolio_df['symbol'] == symbol].iloc[0]
            amount = row['position_value']
            weight = row['weight'] * 100
            all_orders.append({
                'step': f'2.{i}',
                'action': 'BUY',
                'symbol': symbol,
                'amount': f'${amount:.2f}',
                'notes': f'{weight:.2f}% of portfolio'
            })

        # Add rebalances
        for i, symbol in enumerate(sorted(holds), 1):
            row = portfolio_df[portfolio_df['symbol'] == symbol].iloc[0]
            amount = row['position_value']
            weight = row['weight'] * 100
            all_orders.append({
                'step': f'3.{i}',
                'action': 'ADJUST',
                'symbol': symbol,
                'amount': f'${amount:.2f}',
                'notes': f'Target: {weight:.2f}%'
            })

        orders_df = pd.DataFrame(all_orders)
        csv = orders_df.to_csv(index=False)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        st.download_button(
            label="📥 Download Order List (CSV)",
            data=csv,
            file_name=f"robinhood_orders_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.markdown("💡 **Pro tip**: Print this CSV and check off each order as you execute it!")

        # Save current portfolio for next month
        st.markdown("---")
        st.markdown("### 💾 Save for Next Month")
        st.markdown("After executing these trades, **save this portfolio** to use as 'Current Holdings' next month:")

        portfolio_csv = portfolio_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Current Portfolio (for next month's comparison)",
            data=portfolio_csv,
            file_name=f"my_holdings_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True
        )
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 1rem;'>
    <p>LLM-Enhanced Momentum Strategy Dashboard</p>
    <p>Built with Streamlit | Powered by GPT-4o-mini</p>
    <p>⚠️ For educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)

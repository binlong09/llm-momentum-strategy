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

        # Technical Indicators Dashboard
        st.markdown("---")
        st.subheader("📊 Technical Momentum Indicators")

        if st.button("🔍 Analyze Technical Signals", type="primary"):
            with st.spinner("Analyzing technical indicators..."):
                try:
                    from src.data import DataManager
                    from src.analysis import analyze_stock_technicals

                    dm = DataManager()
                    top_symbols = holdings_df.nlargest(15, 'current_value')['symbol'].tolist() if 'current_value' in holdings_df.columns else holdings_df['symbol'].tolist()[:15]
                    price_data = dm.get_prices(top_symbols, use_cache=True, show_progress=False)

                    # Analyze all stocks
                    technical_results = []
                    for symbol in top_symbols:
                        if symbol in price_data and not price_data[symbol].empty:
                            tech = analyze_stock_technicals(price_data[symbol])
                            if tech:
                                weight = holdings_df[holdings_df['symbol'] == symbol]['current_weight'].iloc[0] * 100 if 'current_weight' in holdings_df.columns else 0
                                tech['symbol'] = symbol
                                tech['weight'] = weight
                                technical_results.append(tech)

                    # Store in session state
                    st.session_state.technical_results = technical_results

                    st.success("✅ Technical analysis complete!")

                except Exception as e:
                    st.error(f"Error analyzing technicals: {e}")

        # Display technical results
        if 'technical_results' in st.session_state:
            tech_results = st.session_state.technical_results

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            overbought = [t for t in tech_results if t.get('rsi_signal') == 'OVERBOUGHT']
            oversold = [t for t in tech_results if t.get('rsi_signal') == 'OVERSOLD']
            decelerating = [t for t in tech_results if t.get('momentum', {}).get('status') == 'DECELERATING']
            death_cross = [t for t in tech_results if t.get('moving_averages', {}).get('ma_cross') == 'DEATH_CROSS']

            with col1:
                st.metric("Overbought (RSI>70)", len(overbought))
                if len(overbought) > 0:
                    st.caption("⚠️ May pullback")

            with col2:
                st.metric("Oversold (RSI<30)", len(oversold))
                if len(oversold) > 0:
                    st.caption("💡 Potential reversal")

            with col3:
                st.metric("Decelerating", len(decelerating))
                if len(decelerating) > 0:
                    st.caption("📉 Momentum slowing")

            with col4:
                st.metric("Death Crosses", len(death_cross))
                if len(death_cross) > 0:
                    st.caption("☠️ Major bearish")

            # Detailed breakdown
            with st.expander("📋 Detailed Technical Signals", expanded=True):

                # Critical warnings
                if death_cross:
                    st.error(f"☠️ **DEATH CROSS DETECTED** - {len(death_cross)} stock(s)")
                    for tech in death_cross:
                        st.markdown(f"**{tech['symbol']}** ({tech['weight']:.1f}% of portfolio)")
                        st.caption("50-day MA crossed below 200-day MA - Major bearish signal")
                        st.markdown("---")

                # Decelerating momentum warnings
                if decelerating:
                    st.warning(f"📉 **MOMENTUM DECELERATING** - {len(decelerating)} stock(s)")
                    for tech in sorted(decelerating, key=lambda x: x.get('momentum', {}).get('acceleration', 0)):
                        mom = tech.get('momentum', {})
                        st.markdown(f"**{tech['symbol']}** ({tech['weight']:.1f}%): Momentum slowing {mom.get('acceleration', 0):.2f}%")
                        st.caption(f"Current week: {mom.get('current_week_return', 0):+.2f}%, Prev week: {mom.get('prev_week_return', 0):+.2f}%")
                    st.markdown("---")

                # Overbought warnings
                if overbought:
                    st.warning(f"⚠️ **OVERBOUGHT STOCKS** - {len(overbought)} stock(s)")
                    for tech in sorted(overbought, key=lambda x: x.get('rsi', 0), reverse=True):
                        rsi = tech.get('rsi', 0)
                        mom_status = tech.get('momentum', {}).get('status', 'N/A')
                        st.markdown(f"**{tech['symbol']}** ({tech['weight']:.1f}%): RSI {rsi:.1f}")
                        st.caption(f"Momentum: {mom_status}")
                    st.markdown("---")

                # All stocks table
                st.markdown("### 📊 Full Technical Summary")

                tech_df = pd.DataFrame([
                    {
                        'Symbol': t['symbol'],
                        'Weight%': f"{t['weight']:.1f}%",
                        'RSI': f"{t.get('rsi', 0):.1f}" if 'rsi' in t else 'N/A',
                        'RSI Signal': t.get('rsi_signal', 'N/A'),
                        'Mom Status': t.get('momentum', {}).get('status', 'N/A'),
                        'Mom Accel': f"{t.get('momentum', {}).get('acceleration', 0):+.2f}%" if 'momentum' in t else 'N/A',
                        'MA Cross': t.get('moving_averages', {}).get('ma_cross', 'N/A') if 'moving_averages' in t else 'N/A',
                        'Trend': t.get('moving_averages', {}).get('trend', 'N/A') if 'moving_averages' in t else 'N/A'
                    }
                    for t in tech_results
                ])

                st.dataframe(tech_df, use_container_width=True, hide_index=True)

            # Action items
            if death_cross or (len(decelerating) >= 3) or (len(overbought) >= 3):
                st.markdown("### 🎯 Technical Action Items")

                if death_cross:
                    st.error(f"🚨 **URGENT**: {len(death_cross)} death cross(es) detected - Consider exiting these positions")

                if len(decelerating) >= 3:
                    st.warning(f"⚠️ **CAUTION**: {len(decelerating)} stocks losing momentum - Monitor closely")

                if len(overbought) >= 3:
                    st.info(f"💡 **INFO**: {len(overbought)} overbought stocks - Consider taking some profits")

        # Sector Intelligence Dashboard
        st.markdown("---")
        st.subheader("🎯 Sector Intelligence")

        if st.button("📊 Analyze Sector Exposure", type="primary"):
            with st.spinner("Analyzing sector allocation..."):
                try:
                    from src.data import DataManager
                    from src.analysis import (
                        analyze_sector_concentration,
                        analyze_sector_momentum,
                        detect_sector_rotation,
                        generate_sector_recommendations
                    )

                    dm = DataManager()

                    # Sector concentration
                    concentration = analyze_sector_concentration(holdings_df)

                    # Sector momentum
                    symbols = holdings_df['symbol'].tolist()
                    price_data = dm.get_prices(symbols, use_cache=True, show_progress=False)
                    momentum = analyze_sector_momentum(holdings_df, price_data)

                    # Sector rotation
                    rotation = detect_sector_rotation(momentum)

                    # Recommendations
                    recommendations = generate_sector_recommendations(concentration, momentum, rotation)

                    # Store in session state
                    st.session_state.sector_analysis = {
                        'concentration': concentration,
                        'momentum': momentum,
                        'rotation': rotation,
                        'recommendations': recommendations
                    }

                    st.success("✅ Sector analysis complete!")

                except Exception as e:
                    st.error(f"Error analyzing sectors: {e}")
                    import traceback
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())

        # Display sector results
        if 'sector_analysis' in st.session_state:
            sector_data = st.session_state.sector_analysis
            concentration = sector_data.get('concentration', {})
            momentum = sector_data.get('momentum', {})
            rotation = sector_data.get('rotation', {})
            recommendations = sector_data.get('recommendations', [])

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Top Sector", concentration.get('top_sector', 'N/A'))
                st.caption(f"{concentration.get('top_sector_weight', 0):.1f}% of portfolio")

            with col2:
                st.metric("Diversification", f"{concentration.get('diversification_score', 0):.0f}/100")
                if concentration.get('diversification_score', 0) < 50:
                    st.caption("⚠️ Low diversity")
                else:
                    st.caption("✅ Well diversified")

            with col3:
                st.metric("# Sectors", concentration.get('num_sectors', 0))
                st.caption(f"{concentration.get('concentration_level', 'N/A')} concentration")

            with col4:
                if momentum and 'momentum_spread' in momentum:
                    st.metric("Sector Spread", f"{momentum.get('momentum_spread', 0):.1f}%")
                    st.caption("Leader vs Laggard")
                else:
                    st.metric("Sector Spread", "N/A")

            # Sector breakdown
            with st.expander("📊 Sector Breakdown", expanded=True):

                if concentration and 'sector_weights' in concentration:
                    sector_weights = concentration['sector_weights']

                    # Sector table
                    sector_df_data = []
                    for sector, weight in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True):
                        # Get momentum if available
                        sector_mom = 'N/A'
                        if momentum and 'sector_momentum' in momentum:
                            if sector in momentum['sector_momentum']:
                                sector_mom = f"{momentum['sector_momentum'][sector]['momentum']:+.1f}%"

                        sector_df_data.append({
                            'Sector': sector,
                            'Weight': f"{weight:.1f}%",
                            '1-Month Momentum': sector_mom,
                            'Status': '⚠️ Overweight' if weight > 30 else '✅ Normal' if weight > 5 else 'ℹ️ Underweight'
                        })

                    sector_df = pd.DataFrame(sector_df_data)
                    st.dataframe(sector_df, use_container_width=True, hide_index=True)

                    # Pie chart
                    import plotly.graph_objects as go

                    fig = go.Figure(data=[go.Pie(
                        labels=list(sector_weights.keys()),
                        values=list(sector_weights.values()),
                        hole=0.3
                    )])
                    fig.update_layout(
                        title="Portfolio Sector Allocation",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Sector momentum
            if momentum and 'sector_momentum' in momentum:
                with st.expander("🚀 Sector Momentum Rankings", expanded=False):
                    sector_mom = momentum['sector_momentum']

                    # Leaders
                    st.markdown("### 📈 Leading Sectors")
                    leaders = sorted(sector_mom.items(), key=lambda x: x[1]['momentum'], reverse=True)[:3]
                    for sector, data in leaders:
                        st.markdown(f"**{sector}**: {data['momentum']:+.1f}% momentum ({data['weight']:.1f}% of your portfolio)")

                    st.markdown("---")

                    # Laggards
                    st.markdown("### 📉 Lagging Sectors")
                    laggards = sorted(sector_mom.items(), key=lambda x: x[1]['momentum'])[:3]
                    for sector, data in laggards:
                        st.markdown(f"**{sector}**: {data['momentum']:+.1f}% momentum ({data['weight']:.1f}% of your portfolio)")

            # Rotation detection
            if rotation and rotation.get('rotation_detected'):
                st.warning(f"🔄 **SECTOR ROTATION DETECTED**: {rotation.get('rotation_description')}")

            # Recommendations
            st.markdown("### 🎯 Sector Recommendations")
            for rec in recommendations:
                if '⚠️' in rec or '🚨' in rec:
                    st.warning(rec)
                elif '💡' in rec or 'ℹ️' in rec:
                    st.info(rec)
                elif '📉' in rec or '🔄' in rec:
                    st.warning(rec)
                else:
                    st.success(rec)

        # AI Portfolio Optimizer
        st.markdown("---")
        st.subheader("🤖 AI Portfolio Optimizer")
        st.markdown("Get a definitive rebalancing recommendation based on ALL available signals")

        # Cost warning
        estimated_cost = len(holdings_df) * 0.00066
        st.caption(f"💰 Note: First run will analyze all stocks (~${estimated_cost:.3f} using gpt-4o-mini)")

        if st.button("🎯 Should I Rebalance?", type="primary", use_container_width=True):
            try:
                from src.optimization import PortfolioOptimizer
                from src.data import DataManager
                from src.llm import LLMScorer, LLMRiskScorer

                # Check if we need to run batch analysis first
                need_batch_analysis = 'batch_analysis_results' not in st.session_state

                if need_batch_analysis:
                    with st.spinner(f"🔬 Running AI analysis on {len(holdings_df)} stocks first... This will take ~{len(holdings_df) * 3} seconds..."):
                        dm = DataManager()
                        llm_scorer = LLMScorer(model="gpt-4o-mini")
                        risk_scorer = LLMRiskScorer(model="gpt-4o-mini")

                        # Initialize results storage
                        batch_results = []
                        symbols = holdings_df['symbol'].tolist()

                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for idx, symbol in enumerate(symbols):
                            status_text.text(f"Analyzing {symbol} ({idx+1}/{len(symbols)})...")

                            result = {
                                'symbol': symbol,
                                'current_value': holdings_df[holdings_df['symbol'] == symbol]['current_value'].iloc[0] if 'current_value' in holdings_df.columns else None,
                                'current_weight': holdings_df[holdings_df['symbol'] == symbol]['current_weight'].iloc[0] * 100 if 'current_weight' in holdings_df.columns else None,
                                'price_change_pct': holdings_df[holdings_df['symbol'] == symbol]['price_change_pct'].iloc[0] if 'price_change_pct' in holdings_df.columns else None,
                            }

                            try:
                                # Fetch data
                                price_data = dm.get_prices([symbol], use_cache=True, show_progress=False)
                                news_articles = dm.get_news([symbol], lookback_days=5, use_cache=True).get(symbol, [])
                                earnings_data = dm.get_earnings_for_symbol(symbol, use_cache=True)
                                analyst_data = dm.get_analyst_data_for_symbol(symbol, use_cache=True)

                                # Calculate momentum
                                momentum_return = None
                                if symbol in price_data and not price_data[symbol].empty:
                                    prices = price_data[symbol]
                                    if 'adjusted_close' in prices.columns and len(prices) >= 252:
                                        start_price = prices['adjusted_close'].iloc[-252]
                                        end_price = prices['adjusted_close'].iloc[-1]
                                        momentum_return = (end_price / start_price) - 1

                                # LLM Sentiment Analysis
                                try:
                                    from src.llm.prompts import PromptTemplate
                                    news_summary = PromptTemplate.format_news_for_prompt(
                                        news_articles,
                                        max_articles=20,
                                        max_chars=3000,
                                        prioritize_important=True
                                    )

                                    llm_result = llm_scorer.score_stock(
                                        symbol=symbol,
                                        news_summary=news_summary,
                                        momentum_return=momentum_return,
                                        earnings_data=earnings_data,
                                        analyst_data=analyst_data,
                                        return_prompt=False
                                    )
                                    result['sentiment_score'] = llm_result[1]  # normalized_score
                                except Exception as e:
                                    result['sentiment_score'] = None
                                    result['sentiment_error'] = str(e)

                                # Risk Assessment
                                try:
                                    risk_result = risk_scorer.score_stock_risk(
                                        symbol=symbol,
                                        news_articles=news_articles,
                                        max_articles=10,
                                        return_prompt=False
                                    )
                                    result['risk_score'] = risk_result['overall_risk_score']
                                    result['key_risk'] = risk_result.get('key_risk', 'None')
                                    result['risk_recommendation'] = risk_result.get('recommendation', 'N/A')
                                except Exception as e:
                                    result['risk_score'] = None
                                    result['risk_error'] = str(e)

                                result['status'] = 'success'

                            except Exception as e:
                                result['status'] = 'error'
                                result['error'] = str(e)

                            batch_results.append(result)
                            progress_bar.progress((idx + 1) / len(symbols))

                        # Store results in session state
                        st.session_state.batch_analysis_results = batch_results

                        status_text.text("✅ Stock analysis complete!")
                        progress_bar.empty()

                with st.spinner("🎯 Generating rebalancing recommendation..."):
                    # Gather all signals
                    market_signals = {}
                    portfolio_metrics = {}
                    technical_signals_data = {}
                    sector_data = {}
                    batch_data = {}

                    # Market signals (if available from context building)
                    # We'll extract from session state if available

                    # Portfolio metrics
                    if daily_change:
                        portfolio_metrics['daily_change_pct'] = daily_change.get('change_pct', 0)

                    if 'current_weight' in holdings_df.columns:
                        top3 = holdings_df.nlargest(3, 'current_value')['current_weight'].sum() * 100
                        portfolio_metrics['top3_concentration'] = top3

                    # Technical signals
                    if 'technical_results' in st.session_state:
                        tech = st.session_state.technical_results
                        technical_signals_data['death_crosses'] = [t['symbol'] for t in tech if t.get('moving_averages', {}).get('ma_cross') == 'DEATH_CROSS']
                        technical_signals_data['golden_crosses'] = [t['symbol'] for t in tech if t.get('moving_averages', {}).get('ma_cross') == 'GOLDEN_CROSS']
                        technical_signals_data['overbought'] = [t['symbol'] for t in tech if t.get('rsi_signal') == 'OVERBOUGHT']
                        technical_signals_data['oversold'] = [t['symbol'] for t in tech if t.get('rsi_signal') == 'OVERSOLD']
                        technical_signals_data['decelerating'] = [t['symbol'] for t in tech if t.get('momentum', {}).get('status') == 'DECELERATING']
                        technical_signals_data['accelerating'] = [t['symbol'] for t in tech if t.get('momentum', {}).get('status') == 'ACCELERATING']

                    # Sector analysis
                    if 'sector_analysis' in st.session_state:
                        sector_data = st.session_state.sector_analysis

                    # Batch analysis (now guaranteed to exist)
                    if 'batch_analysis_results' in st.session_state:
                        batch_results = st.session_state.batch_analysis_results
                        batch_df = pd.DataFrame(batch_results)
                        batch_data['avg_sentiment'] = batch_df['sentiment_score'].mean() if 'sentiment_score' in batch_df else None
                        batch_data['avg_risk'] = batch_df['risk_score'].mean() if 'risk_score' in batch_df else None
                        batch_data['high_risk_count'] = len(batch_df[batch_df['risk_score'] > 0.7]) if 'risk_score' in batch_df else 0
                        batch_data['bearish_count'] = len(batch_df[batch_df['sentiment_score'] < 0.4]) if 'sentiment_score' in batch_df else 0
                        batch_data['results'] = batch_results

                    # Run optimizer
                    optimizer = PortfolioOptimizer()
                    result = optimizer.analyze_all_signals(
                        market_signals=market_signals,
                        portfolio_metrics=portfolio_metrics,
                        technical_signals=technical_signals_data,
                        sector_analysis=sector_data,
                        batch_analysis=batch_data,
                        holdings_df=holdings_df
                    )

                    # Store result
                    st.session_state.optimizer_result = result

                    st.success("✅ Analysis complete! Recommendation ready below.")

            except Exception as e:
                st.error(f"Error running optimizer: {e}")
                import traceback
                with st.expander("View error details"):
                    st.code(traceback.format_exc())

        # Display optimizer results
        if 'optimizer_result' in st.session_state:
            result = st.session_state.optimizer_result

            recommendation = result['recommendation']
            confidence = result['confidence']
            overall_score = result['overall_score']
            reasoning = result['reasoning']
            stock_actions = result['stock_actions']

            # Main recommendation card
            st.markdown("---")

            if recommendation == "REBALANCE_NOW":
                st.error(f"### 🚨 RECOMMENDATION: REBALANCE NOW")
                st.error(f"**Confidence: {confidence}%**")
                st.markdown("**Action:** Execute rebalancing at your earliest convenience (today/tomorrow)")
            elif recommendation == "CONSIDER_REBALANCING":
                st.warning(f"### ⚠️ RECOMMENDATION: CONSIDER REBALANCING")
                st.warning(f"**Confidence: {confidence}%**")
                st.markdown("**Action:** Review carefully, lean towards rebalancing within next few days")
            elif recommendation == "MONITOR_CLOSELY":
                st.info(f"### 👀 RECOMMENDATION: MONITOR CLOSELY")
                st.info(f"**Confidence: {confidence}%**")
                st.markdown("**Action:** Check daily for changes, be ready to act if signals worsen")
            else:  # WAIT
                st.success(f"### ✅ RECOMMENDATION: WAIT FOR MONTHLY REBALANCE")
                st.success(f"**Confidence: {confidence}%**")
                st.markdown("**Action:** Stay the course, check back in a week")

            # Overall health score
            st.markdown(f"**Portfolio Health Score: {overall_score:.1f}/100**")

            # Progress bar for visual
            if overall_score < 40:
                st.progress(overall_score / 100, text="Poor Health")
            elif overall_score < 60:
                st.progress(overall_score / 100, text="Fair Health")
            else:
                st.progress(overall_score / 100, text="Good Health")

            # Detailed reasoning
            with st.expander("📊 Detailed Analysis", expanded=True):
                for line in reasoning:
                    st.markdown(line)

            # Stock-specific actions
            if stock_actions:
                st.markdown("---")
                st.markdown("### 📋 Stock-Specific Actions")

                # Group by action
                exit_stocks = {k: v for k, v in stock_actions.items() if v['action'] == 'EXIT'}
                reduce_stocks = {k: v for k, v in stock_actions.items() if v['action'] == 'REDUCE'}
                monitor_stocks = {k: v for k, v in stock_actions.items() if v['action'] == 'MONITOR'}

                if exit_stocks:
                    st.error(f"**🚨 EXIT ({len(exit_stocks)} stock(s)):**")
                    for symbol, data in sorted(exit_stocks.items(), key=lambda x: x[1]['confidence'], reverse=True):
                        st.markdown(f"**{symbol}** (confidence: {data['confidence']}%)")
                        for reason in data['reasons']:
                            st.markdown(f"  - {reason}")

                if reduce_stocks:
                    st.warning(f"**⚠️ REDUCE ({len(reduce_stocks)} stock(s)):**")
                    for symbol, data in sorted(reduce_stocks.items(), key=lambda x: x[1]['confidence'], reverse=True):
                        st.markdown(f"**{symbol}** (confidence: {data['confidence']}%)")
                        for reason in data['reasons']:
                            st.markdown(f"  - {reason}")

                if monitor_stocks:
                    st.info(f"**👀 MONITOR ({len(monitor_stocks)} stock(s)):**")
                    for symbol, data in list(monitor_stocks.items())[:5]:  # Show top 5
                        st.markdown(f"**{symbol}**")
                        for reason in data['reasons']:
                            st.markdown(f"  - {reason}")

                # Hold the rest
                hold_count = len(holdings_df) - len(exit_stocks) - len(reduce_stocks) - len(monitor_stocks)
                if hold_count > 0:
                    st.success(f"**✅ HOLD:** {hold_count} other stock(s) looking good")

        # Ask AI Section for Portfolio
        st.markdown("---")
        st.subheader("💬 Ask AI About Your Portfolio")
        st.markdown("Get AI-powered insights about your portfolio and rebalancing decisions")

        # Initialize conversation history for portfolio
        if 'portfolio_ai_conversation_history' not in st.session_state:
            st.session_state.portfolio_ai_conversation_history = []

        # Build portfolio context
        portfolio_context_key = 'portfolio_ai_context'
        if portfolio_context_key not in st.session_state or st.button("🔄 Refresh Portfolio Context"):
            context_parts = [
                "Portfolio Analysis",
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}",
                f"\nNumber of Holdings: {len(holdings_df)}",
            ]

            # Add portfolio value and daily change
            if daily_change:
                context_parts.append(f"Current Portfolio Value: ${daily_change['value_today']:,.2f}")
                context_parts.append(f"Daily Change: ${daily_change['change']:,.2f} ({daily_change['change_pct']:+.2f}%)")
                context_parts.append(f"Previous Value: ${daily_change['value_yesterday']:,.2f}")

            # Add top holdings
            if 'current_value' in holdings_df.columns:
                top_holdings = holdings_df.nlargest(5, 'current_value')
                context_parts.append("\nTop 5 Holdings by Value:")
                for idx, row in top_holdings.iterrows():
                    weight = row.get('current_weight', 0) * 100
                    change = row.get('price_change_pct', 0)
                    context_parts.append(f"- {row['symbol']}: ${row['current_value']:,.2f} ({weight:.1f}% of portfolio, {change:+.2f}% today)")

            # Add top movers
            if 'price_change_pct' in holdings_df.columns:
                top_gainers = holdings_df.nlargest(3, 'price_change_pct')
                top_losers = holdings_df.nsmallest(3, 'price_change_pct')

                context_parts.append("\nTop 3 Gainers Today:")
                for idx, row in top_gainers.iterrows():
                    context_parts.append(f"- {row['symbol']}: {row['price_change_pct']:+.2f}%")

                context_parts.append("\nTop 3 Losers Today:")
                for idx, row in top_losers.iterrows():
                    context_parts.append(f"- {row['symbol']}: {row['price_change_pct']:+.2f}%")

            # Add alerts if available
            if 'alerts' in st.session_state and len(st.session_state.alerts) > 0:
                alerts_df = st.session_state.alerts
                summary = alert_system.summarize_alerts(alerts_df)
                context_parts.append(f"\nAlerts: {summary['critical']} critical, {summary['warnings']} warnings, {summary['info']} info")

                # Add critical alerts
                critical = alert_system.get_critical_actions(alerts_df)
                if len(critical) > 0:
                    context_parts.append("\nCritical Alerts:")
                    for idx, alert in critical.iterrows():
                        context_parts.append(f"- {alert['symbol']}: {alert['message']} (Action: {alert['action']})")

            # Add news sentiment if available
            if 'news_monitoring' in st.session_state:
                news_df = st.session_state.news_monitoring
                critical_news = len(news_df[news_df['alert_level'] == 'critical'])
                warnings = len(news_df[news_df['alert_level'] == 'warning'])
                context_parts.append(f"\nNews: {critical_news} critical, {warnings} warnings from recent news scan")

            # Add performance metrics if available
            if len(snapshots_df) >= 2 and 'error' not in metrics:
                context_parts.append(f"\nPerformance ({period}):")
                context_parts.append(f"- Total Return: {metrics['total_return']*100:.2f}%")
                context_parts.append(f"- Annualized Return: {metrics['annualized_return']*100:.2f}%")
                context_parts.append(f"- Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
                context_parts.append(f"- Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
                if metrics.get('benchmark'):
                    context_parts.append(f"- Alpha vs SPY: {metrics['alpha']*100:.2f}%")

            # ===== TIER 1 SIGNALS FOR ENHANCED AI RECOMMENDATIONS =====

            # 1. Market Fear Gauge (VIX)
            try:
                from src.data import DataManager
                dm = DataManager()
                vix_data = dm.get_prices(['^VIX'], use_cache=True, show_progress=False)
                if '^VIX' in vix_data and not vix_data['^VIX'].empty:
                    current_vix = vix_data['^VIX']['close'].iloc[-1]
                    context_parts.append(f"\nMarket Fear Gauge (VIX): {current_vix:.2f}")
                    if current_vix > 30:
                        context_parts.append("  ⚠️ HIGH VOLATILITY - Elevated market fear (VIX > 30)")
                    elif current_vix > 20:
                        context_parts.append("  ⚡ MODERATE VOLATILITY - Some market uncertainty (VIX 20-30)")
                    else:
                        context_parts.append("  ✅ LOW VOLATILITY - Calm market conditions (VIX < 20)")
            except Exception as e:
                pass  # VIX not critical, skip if unavailable

            # 2. SPY Recent Performance (Market Direction)
            try:
                from src.data import DataManager
                dm = DataManager()
                spy_data = dm.get_prices(['SPY'], use_cache=True, show_progress=False)
                if 'SPY' in spy_data and not spy_data['SPY'].empty:
                    spy_prices = spy_data['SPY']['adjusted_close']
                    if len(spy_prices) >= 21:
                        spy_5d_return = (spy_prices.iloc[-1] / spy_prices.iloc[-6] - 1) * 100
                        spy_20d_return = (spy_prices.iloc[-1] / spy_prices.iloc[-21] - 1) * 100
                        context_parts.append(f"\nMarket Direction (SPY):")
                        context_parts.append(f"- Last 5 days: {spy_5d_return:+.2f}%")
                        context_parts.append(f"- Last 20 days: {spy_20d_return:+.2f}%")

                        # Market trend interpretation
                        if spy_5d_return < -5:
                            context_parts.append("  📉 Market in short-term pullback")
                        elif spy_5d_return > 5:
                            context_parts.append("  📈 Market in short-term rally")

                        if spy_20d_return < -10:
                            context_parts.append("  ⚠️ Market in medium-term downtrend")
                        elif spy_20d_return > 10:
                            context_parts.append("  ✅ Market in medium-term uptrend")
            except Exception as e:
                pass

            # 3. Concentration Risk
            if 'current_weight' in holdings_df.columns and len(holdings_df) >= 3:
                try:
                    top3_weight = holdings_df.nlargest(3, 'current_value')['current_weight'].sum() * 100
                    context_parts.append(f"\nPortfolio Concentration:")
                    context_parts.append(f"- Top 3 holdings: {top3_weight:.1f}% of portfolio")
                    if top3_weight > 50:
                        context_parts.append("  ⚠️ VERY HIGH concentration - significant risk if top holdings decline")
                    elif top3_weight > 40:
                        context_parts.append("  ⚡ HIGH concentration - consider diversification")
                    else:
                        context_parts.append("  ✅ Reasonable diversification")
                except:
                    pass

            # 4. Position Strength (52-week high/low for top holdings)
            if 'symbol' in holdings_df.columns:
                try:
                    from src.data import DataManager
                    dm = DataManager()
                    top_symbols = holdings_df.nlargest(5, 'current_value')['symbol'].tolist()
                    price_data = dm.get_prices(top_symbols, use_cache=True, show_progress=False)

                    weak_positions = []
                    strong_positions = []

                    for symbol in top_symbols:
                        if symbol in price_data and not price_data[symbol].empty:
                            prices = price_data[symbol]['adjusted_close']
                            if len(prices) >= 252:
                                current = prices.iloc[-1]
                                week_52_high = prices.tail(252).max()
                                week_52_low = prices.tail(252).min()
                                pct_from_high = ((current - week_52_high) / week_52_high) * 100
                                pct_from_low = ((current - week_52_low) / week_52_low) * 100

                                if pct_from_high > -5:
                                    strong_positions.append(f"{symbol} (at/near 52w high)")
                                elif pct_from_high < -25:
                                    weak_positions.append(f"{symbol} ({pct_from_high:.1f}% from 52w high)")

                    if strong_positions or weak_positions:
                        context_parts.append("\nPosition Strength (Top Holdings vs 52-Week Range):")
                        if strong_positions:
                            context_parts.append(f"  💪 STRONG: {', '.join(strong_positions)}")
                        if weak_positions:
                            context_parts.append(f"  ⚠️ WEAK: {', '.join(weak_positions)}")
                except:
                    pass

            # 5. Consecutive Down Days (Panic Indicator)
            if len(snapshots_df) >= 5:
                try:
                    consecutive_down = 0
                    consecutive_up = 0

                    # Count consecutive down days
                    for i in range(len(snapshots_df)-1, 0, -1):
                        if snapshots_df.iloc[i]['total_value'] < snapshots_df.iloc[i-1]['total_value']:
                            consecutive_down += 1
                        else:
                            break

                    # Count consecutive up days if not down
                    if consecutive_down == 0:
                        for i in range(len(snapshots_df)-1, 0, -1):
                            if snapshots_df.iloc[i]['total_value'] > snapshots_df.iloc[i-1]['total_value']:
                                consecutive_up += 1
                            else:
                                break

                    if consecutive_down > 0:
                        context_parts.append(f"\nPortfolio Trend: 📉 Down {consecutive_down} consecutive day(s)")
                        if consecutive_down <= 2:
                            context_parts.append("  ℹ️ Normal market fluctuation - no immediate concern")
                        elif consecutive_down <= 4:
                            context_parts.append("  ⚡ Short-term weakness - monitor but typically normal for momentum strategies")
                        else:
                            context_parts.append("  ⚠️ Extended decline - review for potential issues in holdings")
                    elif consecutive_up > 0:
                        context_parts.append(f"\nPortfolio Trend: 📈 Up {consecutive_up} consecutive day(s)")
                        if consecutive_up >= 5:
                            context_parts.append("  ✅ Strong momentum - strategy performing well")
                except:
                    pass

            # 6. Days Since Last Rebalance (if trackable)
            try:
                # Try to infer from snapshot source or metadata
                if len(snapshots_df) > 0:
                    latest_snapshot = snapshots_df.iloc[-1]
                    snapshot_date = pd.to_datetime(latest_snapshot['date'])
                    days_tracked = (datetime.now() - snapshot_date).days

                    # Estimate time in current portfolio (rough heuristic)
                    if days_tracked < 30:
                        context_parts.append(f"\nTime in Current Portfolio: ~{days_tracked} days")
                        if days_tracked < 7:
                            context_parts.append("  ℹ️ Very recent portfolio - give strategy time to work")
                        elif days_tracked >= 25:
                            context_parts.append("  📅 Approaching monthly rebalance window")
            except:
                pass

            # 7. Batch Analysis Results (if available)
            if 'batch_analysis_results' in st.session_state:
                try:
                    batch_df = pd.DataFrame(st.session_state.batch_analysis_results)

                    # Overall portfolio AI metrics
                    avg_sentiment = batch_df['sentiment_score'].mean() if 'sentiment_score' in batch_df else None
                    avg_risk = batch_df['risk_score'].mean() if 'risk_score' in batch_df else None

                    context_parts.append("\n🤖 AI Analysis Results (from batch analysis):")

                    if avg_sentiment is not None:
                        sentiment_label = "BULLISH" if avg_sentiment >= 0.7 else "NEUTRAL" if avg_sentiment >= 0.5 else "BEARISH"
                        context_parts.append(f"- Portfolio Avg Sentiment: {avg_sentiment:.3f} ({sentiment_label})")

                    if avg_risk is not None:
                        risk_label = "LOW RISK" if avg_risk < 0.4 else "MEDIUM RISK" if avg_risk < 0.7 else "HIGH RISK"
                        context_parts.append(f"- Portfolio Avg Risk: {avg_risk:.2f} ({risk_label})")

                    # High risk stocks
                    high_risk_stocks = batch_df[batch_df['risk_score'] > 0.7] if 'risk_score' in batch_df else pd.DataFrame()
                    if len(high_risk_stocks) > 0:
                        context_parts.append(f"\n⚠️ HIGH RISK STOCKS ({len(high_risk_stocks)}):")
                        for _, stock in high_risk_stocks.sort_values('risk_score', ascending=False).head(5).iterrows():
                            weight = stock.get('current_weight', 0)
                            context_parts.append(f"  - {stock['symbol']}: Risk {stock['risk_score']:.2f} ({weight:.1f}% of portfolio)")
                            if 'key_risk' in stock and pd.notna(stock['key_risk']):
                                context_parts.append(f"    Key Risk: {stock['key_risk']}")
                            if 'risk_recommendation' in stock and pd.notna(stock['risk_recommendation']):
                                context_parts.append(f"    Recommendation: {stock['risk_recommendation']}")

                    # Bearish stocks
                    bearish_stocks = batch_df[batch_df['sentiment_score'] < 0.4] if 'sentiment_score' in batch_df else pd.DataFrame()
                    if len(bearish_stocks) > 0:
                        context_parts.append(f"\n📉 BEARISH STOCKS ({len(bearish_stocks)}):")
                        for _, stock in bearish_stocks.sort_values('sentiment_score').head(5).iterrows():
                            weight = stock.get('current_weight', 0)
                            context_parts.append(f"  - {stock['symbol']}: Sentiment {stock['sentiment_score']:.3f} ({weight:.1f}% of portfolio)")

                    # Bullish + Strong stocks
                    strong_stocks = batch_df[
                        (batch_df['sentiment_score'] >= 0.7) &
                        (batch_df['risk_score'] < 0.4)
                    ] if 'sentiment_score' in batch_df and 'risk_score' in batch_df else pd.DataFrame()
                    if len(strong_stocks) > 0:
                        context_parts.append(f"\n✅ STRONG STOCKS ({len(strong_stocks)}) - High sentiment, Low risk:")
                        for _, stock in strong_stocks.sort_values('sentiment_score', ascending=False).head(5).iterrows():
                            weight = stock.get('current_weight', 0)
                            context_parts.append(f"  - {stock['symbol']}: Sentiment {stock['sentiment_score']:.3f}, Risk {stock['risk_score']:.2f} ({weight:.1f}%)")

                except Exception as e:
                    pass  # Batch analysis data might be incomplete

            # 8. Technical Indicators (RSI, Momentum, Volume, MAs) for top holdings
            try:
                from src.data import DataManager
                from src.analysis import analyze_stock_technicals

                dm = DataManager()
                top_symbols = holdings_df.nlargest(10, 'current_value')['symbol'].tolist() if 'current_value' in holdings_df.columns else holdings_df['symbol'].tolist()[:10]
                price_data = dm.get_prices(top_symbols, use_cache=True, show_progress=False)

                context_parts.append("\n📊 Technical Momentum Indicators (Top Holdings):")

                overbought_stocks = []
                oversold_stocks = []
                decelerating_stocks = []
                accelerating_stocks = []
                death_cross_stocks = []
                golden_cross_stocks = []

                for symbol in top_symbols[:10]:  # Analyze top 10
                    if symbol in price_data and not price_data[symbol].empty:
                        tech = analyze_stock_technicals(price_data[symbol])

                        if not tech:
                            continue

                        # RSI signals
                        if 'rsi' in tech:
                            rsi = tech['rsi']
                            if tech.get('rsi_signal') == 'OVERBOUGHT':
                                overbought_stocks.append((symbol, rsi))
                            elif tech.get('rsi_signal') == 'OVERSOLD':
                                oversold_stocks.append((symbol, rsi))

                        # Momentum acceleration signals
                        if 'momentum' in tech:
                            mom = tech['momentum']
                            if mom['status'] == 'DECELERATING':
                                decelerating_stocks.append((symbol, mom['acceleration']))
                            elif mom['status'] == 'ACCELERATING':
                                accelerating_stocks.append((symbol, mom['acceleration']))

                        # Moving average signals
                        if 'moving_averages' in tech:
                            ma = tech['moving_averages']
                            if ma.get('ma_cross') == 'DEATH_CROSS':
                                death_cross_stocks.append(symbol)
                            elif ma.get('ma_cross') == 'GOLDEN_CROSS':
                                golden_cross_stocks.append(symbol)

                # Report findings
                if overbought_stocks:
                    context_parts.append(f"\n⚠️ OVERBOUGHT (RSI >70): {len(overbought_stocks)} stock(s)")
                    for symbol, rsi in sorted(overbought_stocks, key=lambda x: x[1], reverse=True)[:3]:
                        context_parts.append(f"  - {symbol}: RSI {rsi:.1f} (may be due for pullback)")

                if oversold_stocks:
                    context_parts.append(f"\n💡 OVERSOLD (RSI <30): {len(oversold_stocks)} stock(s)")
                    for symbol, rsi in sorted(oversold_stocks, key=lambda x: x[1])[:3]:
                        context_parts.append(f"  - {symbol}: RSI {rsi:.1f} (potential reversal opportunity)")

                if decelerating_stocks:
                    context_parts.append(f"\n📉 MOMENTUM DECELERATING: {len(decelerating_stocks)} stock(s)")
                    for symbol, accel in sorted(decelerating_stocks, key=lambda x: x[1])[:3]:
                        context_parts.append(f"  - {symbol}: Momentum slowing {accel:.2f}% (early warning)")

                if accelerating_stocks:
                    context_parts.append(f"\n🚀 MOMENTUM ACCELERATING: {len(accelerating_stocks)} stock(s)")
                    for symbol, accel in sorted(accelerating_stocks, key=lambda x: x[1], reverse=True)[:3]:
                        context_parts.append(f"  - {symbol}: Momentum increasing +{accel:.2f}% (strengthening)")

                if death_cross_stocks:
                    context_parts.append(f"\n☠️ DEATH CROSS (50MA < 200MA): {', '.join(death_cross_stocks)}")
                    context_parts.append("  ⚠️ Bearish technical signal - momentum may be breaking")

                if golden_cross_stocks:
                    context_parts.append(f"\n✨ GOLDEN CROSS (50MA > 200MA): {', '.join(golden_cross_stocks)}")
                    context_parts.append("  ✅ Bullish technical signal - strong trend confirmed")

                # Summary
                if not any([overbought_stocks, oversold_stocks, decelerating_stocks, death_cross_stocks]):
                    context_parts.append("\n✅ Technical indicators look healthy - no major warnings")

            except Exception as e:
                pass  # Technical indicators not critical

            # 9. Sector Intelligence (if available)
            if 'sector_analysis' in st.session_state:
                try:
                    sector_data = st.session_state.sector_analysis
                    concentration = sector_data.get('concentration', {})
                    momentum = sector_data.get('momentum', {})
                    rotation = sector_data.get('rotation', {})
                    recommendations = sector_data.get('recommendations', [])

                    context_parts.append("\n🎯 Sector Intelligence:")

                    # Concentration
                    if concentration:
                        top_sector = concentration.get('top_sector', 'N/A')
                        top_weight = concentration.get('top_sector_weight', 0)
                        div_score = concentration.get('diversification_score', 0)
                        conc_level = concentration.get('concentration_level', 'N/A')

                        context_parts.append(f"- Top Sector: {top_sector} ({top_weight:.1f}% of portfolio)")
                        context_parts.append(f"- Diversification Score: {div_score:.0f}/100 ({conc_level} concentration)")
                        context_parts.append(f"- Number of Sectors: {concentration.get('num_sectors', 0)}")

                    # Sector momentum
                    if momentum and 'sector_momentum' in momentum:
                        leading = momentum.get('leading_sector')
                        lagging = momentum.get('lagging_sector')
                        spread = momentum.get('momentum_spread', 0)

                        context_parts.append(f"\nSector Momentum:")
                        context_parts.append(f"- Leading Sector: {leading}")
                        context_parts.append(f"- Lagging Sector: {lagging}")
                        context_parts.append(f"- Leader-Laggard Spread: {spread:.1f}%")

                        # Detail on sectors with significant exposure
                        sector_mom = momentum['sector_momentum']
                        for sector, data in sorted(sector_mom.items(), key=lambda x: x[1]['weight'], reverse=True)[:3]:
                            if data['weight'] > 10:  # Only report if >10% of portfolio
                                context_parts.append(f"  - {sector}: {data['momentum']:+.1f}% momentum ({data['weight']:.1f}% of portfolio)")

                    # Rotation
                    if rotation and rotation.get('rotation_detected'):
                        context_parts.append(f"\n🔄 SECTOR ROTATION: {rotation.get('rotation_description')}")

                    # Recommendations
                    if recommendations:
                        context_parts.append("\nSector Recommendations:")
                        for rec in recommendations[:3]:  # Top 3 recommendations
                            context_parts.append(f"  {rec}")

                except Exception as e:
                    pass  # Sector analysis not critical

            st.session_state[portfolio_context_key] = "\n".join(context_parts)

        # Display conversation history
        if st.session_state.portfolio_ai_conversation_history:
            with st.expander("📜 Conversation History", expanded=False):
                for i, msg in enumerate(st.session_state.portfolio_ai_conversation_history):
                    role = msg['role']
                    content = msg['content']
                    if role == 'user':
                        st.markdown(f"**You:** {content}")
                    else:
                        st.markdown(f"**AI:** {content}")
                    if i < len(st.session_state.portfolio_ai_conversation_history) - 1:
                        st.markdown("---")

        # Question input with form
        with st.form(key="portfolio_ask_ai_form", clear_on_submit=True):
            portfolio_question = st.text_area(
                "Ask a question about your portfolio:",
                placeholder="e.g., There seems to be a lot of fear in the market now, should I rebalance sooner than expected? Should I hold or reduce my positions?",
                height=100,
                key="portfolio_ai_question_input"
            )

            col1, col2 = st.columns([1, 5])
            with col1:
                portfolio_submit_button = st.form_submit_button("Ask AI", type="primary")
            with col2:
                if st.form_submit_button("Clear History"):
                    st.session_state.portfolio_ai_conversation_history = []
                    st.rerun()

        # Process question when submitted
        if portfolio_submit_button and portfolio_question.strip():
            with st.spinner("AI is analyzing your portfolio..."):
                try:
                    from openai import OpenAI
                    import os
                    import yaml

                    # Initialize OpenAI client
                    api_key = None

                    # Try Streamlit secrets first
                    try:
                        if hasattr(st, 'secrets') and 'openai' in st.secrets:
                            api_key = st.secrets['openai'].get('api_key')
                    except:
                        pass

                    # Try environment variable
                    if not api_key:
                        api_key = os.getenv('OPENAI_API_KEY')

                    # Try config file
                    if not api_key:
                        try:
                            with open('config/api_keys.yaml', 'r') as f:
                                config = yaml.safe_load(f)
                                api_key = config.get('openai', {}).get('api_key')
                        except:
                            pass

                    if not api_key:
                        st.error("OpenAI API key not found. Please configure it in Streamlit secrets, environment, or config file.")
                    else:
                        client = OpenAI(api_key=api_key)

                        # Build messages for API call
                        messages = [
                            {
                                "role": "system",
                                "content": f"""You are a helpful financial portfolio advisor assistant specializing in momentum investing strategies. You have access to the user's comprehensive portfolio data including market signals:

{st.session_state[portfolio_context_key]}

KEY SIGNALS TO CONSIDER IN YOUR ADVICE:

1. **VIX (Market Fear Gauge)**:
   - VIX > 30 = High fear, but also potential opportunity for disciplined investors
   - VIX 20-30 = Normal volatility, stay the course
   - VIX < 20 = Low fear, smooth sailing

2. **Market Direction (SPY)**:
   - Use 5-day and 20-day returns to gauge short vs medium-term trends
   - Short-term pullbacks are normal; medium-term downtrends warrant closer monitoring

3. **Portfolio Concentration**:
   - Top 3 > 50% = High risk, diversification needed
   - Top 3 > 40% = Elevated risk, watch closely
   - Consider this when recommending holds vs rebalancing

4. **Position Strength (52-week high/low)**:
   - Positions near 52w highs = Strong momentum, keep riding
   - Positions >25% below 52w highs = Weakening momentum, may need replacement

5. **Consecutive Down Days**:
   - 1-2 days down = Normal noise, ignore
   - 3-4 days down = Short-term weakness, typically normal for momentum
   - 5+ days down = Extended decline, investigate underlying issues

6. **Time in Portfolio**:
   - <7 days = Too early to judge, give it time
   - 25-30 days = Approaching monthly rebalance window
   - Consider holding pattern until scheduled rebalance unless critical issues

7. **AI Batch Analysis Results** (if available):
   - Portfolio Avg Sentiment: Overall bullish/neutral/bearish signal
   - Portfolio Avg Risk: Overall risk level
   - High Risk Stocks: Individual positions with concerning risk scores (>0.7)
   - Bearish Stocks: Positions with low sentiment (<0.4), momentum may be breaking
   - Strong Stocks: High sentiment + low risk = ideal momentum positions
   - PRIORITIZE stock-specific AI insights over market-wide fear when making decisions

8. **Technical Momentum Indicators** (if available):
   - RSI Overbought (>70): Stock may be due for pullback, but in strong uptrends can stay overbought
   - RSI Oversold (<30): Potential reversal opportunity, but avoid catching falling knives
   - Momentum Decelerating: Early warning sign - watch closely, momentum may be breaking
   - Momentum Accelerating: Strengthening trend - high confidence in continuation
   - Death Cross (50MA < 200MA): MAJOR bearish signal - consider exiting position
   - Golden Cross (50MA > 200MA): MAJOR bullish signal - trend confirmed strong
   - TECHNICAL signals confirm or contradict fundamental/sentiment analysis

9. **Sector Intelligence** (if available):
   - Concentration >40% in one sector = HIGH RISK - sector-specific events could tank portfolio
   - Diversification Score <50 = Poor diversification - too concentrated
   - Sector Rotation = Market regime changing - adjust allocations accordingly
   - Heavy exposure to lagging sector = Drag on performance - consider rotation
   - Heavy exposure to leading sector = Riding the trend - but watch for exhaustion
   - Use sector analysis to avoid over-concentration and catch rotation early

REBALANCING DECISION FRAMEWORK:

**WAIT for monthly rebalance if**:
- VIX elevated but no critical alerts
- Only 1-4 consecutive down days
- Strong positions still holding
- Time in portfolio < 25 days
- Market in normal pullback (not crash)
- Avg portfolio sentiment > 0.5 (neutral to bullish)
- Avg portfolio risk < 0.6 (manageable risk)
- Few/no high-risk or bearish stocks in batch analysis
- Sector concentration < 50% in top sector
- Diversification score > 40
- No major sector rotation detected

**CONSIDER early rebalancing if**:
- Multiple critical alerts on top holdings
- High concentration (>50%) + top holdings showing weakness (>25% from 52w high)
- 5+ consecutive down days + multiple weak positions
- Clear evidence momentum has broken (not just fear)
- VIX spike + major position-specific issues
- Batch analysis shows: 3+ high-risk stocks OR avg portfolio risk > 0.7
- Batch analysis shows: Multiple bearish stocks that are large positions (>5% each)
- Avg portfolio sentiment < 0.4 (broadly bearish across holdings)
- Technical signals: 2+ death crosses in top holdings (momentum clearly broken)
- Technical signals: 3+ stocks with decelerating momentum + high RSI (exhaustion pattern)
- Technical signals: Top holding in death cross + bearish sentiment + high risk (triple confirmation)
- Sector analysis: >60% concentrated in ONE sector (extreme risk)
- Sector analysis: >40% in LAGGING sector (negative momentum drag)
- Sector analysis: Major rotation detected + you're heavy in fading sectors (misaligned with market)

**GENERAL PHILOSOPHY**:
- Momentum strategies require discipline and time to work
- Market fear (high VIX) ≠ bad strategy, often creates opportunities
- Monthly rebalancing is optimal; excessive trading hurts returns
- Position-specific issues (earnings miss, critical news) > market-wide fear
- Always weigh transaction costs and tax implications of early rebalancing

Provide thoughtful, balanced advice using these signals. Reference specific data points from the context. Always remind the user to consider their own risk tolerance, investment timeline, and financial situation."""
                            }
                        ]

                        # Add conversation history
                        for msg in st.session_state.portfolio_ai_conversation_history:
                            messages.append({"role": msg["role"], "content": msg["content"]})

                        # Add current question
                        messages.append({"role": "user", "content": portfolio_question})

                        # Call OpenAI API
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages,
                            temperature=0.7,
                            max_tokens=1000
                        )

                        ai_response = response.choices[0].message.content

                        # Update conversation history
                        st.session_state.portfolio_ai_conversation_history.append({
                            "role": "user",
                            "content": portfolio_question
                        })
                        st.session_state.portfolio_ai_conversation_history.append({
                            "role": "assistant",
                            "content": ai_response
                        })

                        # Display the response
                        st.markdown("**AI Response:**")
                        st.info(ai_response)

                except Exception as e:
                    st.error(f"Error calling AI: {e}")
                    import traceback
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())

        # Batch Analysis Section
        st.markdown("---")
        st.subheader("🔬 Analyze All Stocks in Portfolio")
        st.markdown("Run comprehensive AI analysis on every holding (LLM Sentiment + Risk Assessment)")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(f"💰 Estimated cost: ~${len(holdings_df) * 0.00066:.3f} (using gpt-4o-mini)")
            st.caption(f"⏱️ Estimated time: ~{len(holdings_df) * 3} seconds for {len(holdings_df)} stocks")
        with col2:
            batch_model = st.selectbox(
                "Model",
                ["gpt-4o-mini", "gpt-4o"],
                index=0,
                key="batch_model",
                help="gpt-4o-mini is fastest and cheapest"
            )

        if st.button("🚀 Analyze All Stocks", type="primary", use_container_width=True):
            with st.spinner(f"Analyzing {len(holdings_df)} stocks... This may take a minute..."):
                try:
                    from src.data import DataManager
                    from src.llm import LLMScorer, LLMRiskScorer

                    dm = DataManager()
                    llm_scorer = LLMScorer(model=batch_model)
                    risk_scorer = LLMRiskScorer(model=batch_model)

                    # Initialize results storage
                    batch_results = []
                    symbols = holdings_df['symbol'].tolist()

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    for idx, symbol in enumerate(symbols):
                        status_text.text(f"Analyzing {symbol} ({idx+1}/{len(symbols)})...")

                        result = {
                            'symbol': symbol,
                            'current_value': holdings_df[holdings_df['symbol'] == symbol]['current_value'].iloc[0] if 'current_value' in holdings_df.columns else None,
                            'current_weight': holdings_df[holdings_df['symbol'] == symbol]['current_weight'].iloc[0] * 100 if 'current_weight' in holdings_df.columns else None,
                            'price_change_pct': holdings_df[holdings_df['symbol'] == symbol]['price_change_pct'].iloc[0] if 'price_change_pct' in holdings_df.columns else None,
                        }

                        try:
                            # Fetch data
                            price_data = dm.get_prices([symbol], use_cache=True, show_progress=False)
                            news_articles = dm.get_news([symbol], lookback_days=5, use_cache=True).get(symbol, [])
                            earnings_data = dm.get_earnings_for_symbol(symbol, use_cache=True)
                            analyst_data = dm.get_analyst_data_for_symbol(symbol, use_cache=True)

                            # Calculate momentum
                            momentum_return = None
                            if symbol in price_data and not price_data[symbol].empty:
                                prices = price_data[symbol]
                                if 'adjusted_close' in prices.columns and len(prices) >= 252:
                                    start_price = prices['adjusted_close'].iloc[-252]
                                    end_price = prices['adjusted_close'].iloc[-1]
                                    momentum_return = (end_price / start_price) - 1

                            # LLM Sentiment Analysis
                            try:
                                from src.llm.prompts import PromptTemplate
                                news_summary = PromptTemplate.format_news_for_prompt(
                                    news_articles,
                                    max_articles=20,
                                    max_chars=3000,
                                    prioritize_important=True
                                )

                                llm_result = llm_scorer.score_stock(
                                    symbol=symbol,
                                    news_summary=news_summary,
                                    momentum_return=momentum_return,
                                    earnings_data=earnings_data,
                                    analyst_data=analyst_data,
                                    return_prompt=False
                                )
                                result['sentiment_score'] = llm_result[1]  # normalized_score
                            except Exception as e:
                                result['sentiment_score'] = None
                                result['sentiment_error'] = str(e)

                            # Risk Assessment
                            try:
                                risk_result = risk_scorer.score_stock_risk(
                                    symbol=symbol,
                                    news_articles=news_articles,
                                    max_articles=10,
                                    return_prompt=False
                                )
                                result['risk_score'] = risk_result['overall_risk_score']
                                result['key_risk'] = risk_result.get('key_risk', 'None')
                                result['risk_recommendation'] = risk_result.get('recommendation', 'N/A')
                            except Exception as e:
                                result['risk_score'] = None
                                result['risk_error'] = str(e)

                            result['status'] = 'success'

                        except Exception as e:
                            result['status'] = 'error'
                            result['error'] = str(e)

                        batch_results.append(result)
                        progress_bar.progress((idx + 1) / len(symbols))

                    # Store results in session state
                    st.session_state.batch_analysis_results = batch_results

                    status_text.text("✅ Analysis complete!")
                    progress_bar.empty()

                    st.success(f"Successfully analyzed {len(batch_results)} stocks!")

                except Exception as e:
                    st.error(f"Batch analysis failed: {e}")
                    import traceback
                    with st.expander("View error details"):
                        st.code(traceback.format_exc())

        # Display batch results if available
        if 'batch_analysis_results' in st.session_state:
            st.markdown("---")
            st.markdown("### 📊 Portfolio Analysis Summary")

            results_df = pd.DataFrame(st.session_state.batch_analysis_results)

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_sentiment = results_df['sentiment_score'].mean() if 'sentiment_score' in results_df else None
                if avg_sentiment is not None:
                    st.metric("Avg Sentiment", f"{avg_sentiment:.3f}")
                    if avg_sentiment >= 0.7:
                        st.caption("🟢 Bullish Portfolio")
                    elif avg_sentiment >= 0.5:
                        st.caption("🟡 Neutral Portfolio")
                    else:
                        st.caption("🔴 Cautious Portfolio")
                else:
                    st.metric("Avg Sentiment", "N/A")

            with col2:
                avg_risk = results_df['risk_score'].mean() if 'risk_score' in results_df else None
                if avg_risk is not None:
                    st.metric("Avg Risk", f"{avg_risk:.2f}")
                    if avg_risk < 0.4:
                        st.caption("🟢 Low Risk")
                    elif avg_risk < 0.7:
                        st.caption("🟡 Medium Risk")
                    else:
                        st.caption("🔴 High Risk")
                else:
                    st.metric("Avg Risk", "N/A")

            with col3:
                high_risk_count = len(results_df[results_df['risk_score'] > 0.7]) if 'risk_score' in results_df else 0
                st.metric("High Risk Stocks", high_risk_count)
                if high_risk_count > 0:
                    st.caption("⚠️ Review these")

            with col4:
                low_sentiment_count = len(results_df[results_df['sentiment_score'] < 0.4]) if 'sentiment_score' in results_df else 0
                st.metric("Bearish Stocks", low_sentiment_count)
                if low_sentiment_count > 0:
                    st.caption("⚠️ Monitor closely")

            # Detailed results table
            with st.expander("📋 View Detailed Results", expanded=True):
                # Create display dataframe
                display_df = results_df.copy()

                # Format columns
                if 'current_weight' in display_df.columns:
                    display_df['weight_%'] = display_df['current_weight'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
                if 'price_change_pct' in display_df.columns:
                    display_df['today_%'] = display_df['price_change_pct'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
                if 'sentiment_score' in display_df.columns:
                    display_df['sentiment'] = display_df['sentiment_score'].apply(
                        lambda x: f"{x:.3f} {'🟢' if x >= 0.7 else '🟡' if x >= 0.5 else '🔴'}" if pd.notna(x) else "N/A"
                    )
                if 'risk_score' in display_df.columns:
                    display_df['risk'] = display_df['risk_score'].apply(
                        lambda x: f"{x:.2f} {'🟢' if x < 0.4 else '🟡' if x < 0.7 else '🔴'}" if pd.notna(x) else "N/A"
                    )

                # Select columns to display
                display_cols = ['symbol']
                if 'weight_%' in display_df.columns:
                    display_cols.append('weight_%')
                if 'today_%' in display_df.columns:
                    display_cols.append('today_%')
                if 'sentiment' in display_df.columns:
                    display_cols.append('sentiment')
                if 'risk' in display_df.columns:
                    display_cols.append('risk')
                if 'risk_recommendation' in display_df.columns:
                    display_cols.append('risk_recommendation')

                st.dataframe(
                    display_df[display_cols],
                    use_container_width=True,
                    hide_index=True
                )

            # Action items
            st.markdown("### 🎯 Action Items")

            # High risk stocks
            if 'risk_score' in results_df.columns:
                high_risk_stocks = results_df[results_df['risk_score'] > 0.7].sort_values('risk_score', ascending=False)
                if len(high_risk_stocks) > 0:
                    st.warning(f"⚠️ **{len(high_risk_stocks)} High-Risk Stock(s) Detected**")
                    for _, stock in high_risk_stocks.iterrows():
                        st.markdown(f"- **{stock['symbol']}**: Risk {stock['risk_score']:.2f} - {stock.get('key_risk', 'N/A')}")
                        st.caption(f"  Recommendation: {stock.get('risk_recommendation', 'N/A')}")

            # Low sentiment stocks
            if 'sentiment_score' in results_df.columns:
                low_sentiment_stocks = results_df[results_df['sentiment_score'] < 0.4].sort_values('sentiment_score')
                if len(low_sentiment_stocks) > 0:
                    st.warning(f"📉 **{len(low_sentiment_stocks)} Bearish Stock(s) Detected**")
                    for _, stock in low_sentiment_stocks.iterrows():
                        st.markdown(f"- **{stock['symbol']}**: Sentiment {stock['sentiment_score']:.3f}")

            # All clear message
            if (high_risk_count == 0 and low_sentiment_count == 0):
                st.success("✅ **Portfolio looks healthy!** No major concerns detected.")

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

                        # Ask AI Section
                        st.markdown("---")
                        st.subheader("💬 Ask AI")
                        st.markdown("Ask questions about this stock analysis and get AI-powered insights")

                        # Initialize conversation history in session state
                        if 'ai_conversation_history' not in st.session_state:
                            st.session_state.ai_conversation_history = []

                        # Initialize analysis context in session state (preserves the current analysis)
                        context_key = f'ai_analysis_context_{ticker}'
                        if context_key not in st.session_state:
                            # Build context from current analysis
                            context_parts = [
                                f"Stock: {ticker}",
                                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}",
                            ]

                            # Add momentum data
                            if momentum_return is not None:
                                context_parts.append(f"12-Month Momentum: {momentum_return*100:.2f}%")
                            if momentum_return is not None and spy_momentum is not None:
                                relative_perf = (momentum_return - spy_momentum) * 100
                                context_parts.append(f"Performance vs SPY: {relative_perf:+.2f}%")

                            # Add news summary
                            if news_articles:
                                context_parts.append(f"\nRecent News ({len(news_articles)} articles):")
                                # Limit news context to first 5 articles
                                for i, article in enumerate(news_articles[:5], 1):
                                    article_text = article[:150] + "..." if len(article) > 150 else article
                                    context_parts.append(f"{i}. {article_text}")

                            # Add earnings data
                            if earnings_data:
                                context_parts.append("\nEarnings & Fundamentals:")
                                if earnings_data.get('latest_eps') is not None:
                                    context_parts.append(f"- Latest EPS: ${earnings_data['latest_eps']:.2f}")
                                if earnings_data.get('yoy_eps_growth') is not None:
                                    context_parts.append(f"- YoY EPS Growth: {earnings_data['yoy_eps_growth']*100:+.1f}%")
                                if earnings_data.get('profit_margin') is not None:
                                    context_parts.append(f"- Profit Margin: {earnings_data['profit_margin']*100:.1f}%")

                            # Add analyst data
                            if analyst_data:
                                context_parts.append("\nAnalyst Ratings:")
                                if analyst_data.get('recommendation'):
                                    context_parts.append(f"- Consensus: {analyst_data['recommendation']}")
                                if analyst_data.get('target_mean_price'):
                                    context_parts.append(f"- Price Target: ${analyst_data['target_mean_price']:.2f}")
                                if analyst_data.get('upside_potential') is not None:
                                    context_parts.append(f"- Upside Potential: {analyst_data['upside_potential']*100:+.1f}%")

                            # Add LLM sentiment if available
                            if run_llm and normalized_score is not None:
                                context_parts.append(f"\nLLM Sentiment Score: {normalized_score:.3f}")
                                if use_research_mode and analysis:
                                    context_parts.append(f"AI Analysis: {analysis}")

                            # Add risk assessment if available
                            if run_risk and risk_score is not None:
                                context_parts.append(f"\nRisk Score: {risk_score:.2f}")
                                context_parts.append(f"Key Risk: {key_risk}")
                                context_parts.append(f"Recommendation: {risk_result.get('recommendation', 'N/A')}")

                            st.session_state[context_key] = "\n".join(context_parts)

                        # Display conversation history
                        if st.session_state.ai_conversation_history:
                            with st.expander("📜 Conversation History", expanded=False):
                                for i, msg in enumerate(st.session_state.ai_conversation_history):
                                    role = msg['role']
                                    content = msg['content']
                                    if role == 'user':
                                        st.markdown(f"**You:** {content}")
                                    else:
                                        st.markdown(f"**AI:** {content}")
                                    if i < len(st.session_state.ai_conversation_history) - 1:
                                        st.markdown("---")

                        # Question input with form to prevent state clearing
                        with st.form(key="ask_ai_form", clear_on_submit=True):
                            user_question = st.text_area(
                                "Ask a question:",
                                placeholder="e.g., There seems to be a lot of fear now, should I hold, sell, or buy more?",
                                height=100,
                                key="ai_question_input"
                            )

                            col1, col2 = st.columns([1, 5])
                            with col1:
                                submit_button = st.form_submit_button("Ask AI", type="primary")
                            with col2:
                                if st.form_submit_button("Clear History"):
                                    st.session_state.ai_conversation_history = []
                                    st.rerun()

                        # Process question when submitted
                        if submit_button and user_question.strip():
                            with st.spinner("AI is thinking..."):
                                try:
                                    from openai import OpenAI

                                    # Initialize OpenAI client (same pattern as LLMScorer)
                                    api_key = None

                                    # Try Streamlit secrets first
                                    try:
                                        if hasattr(st, 'secrets') and 'openai' in st.secrets:
                                            api_key = st.secrets['openai'].get('api_key')
                                    except:
                                        pass

                                    # Try environment variable
                                    if not api_key:
                                        import os
                                        api_key = os.getenv('OPENAI_API_KEY')

                                    # Try config file
                                    if not api_key:
                                        import yaml
                                        try:
                                            with open('config/api_keys.yaml', 'r') as f:
                                                config = yaml.safe_load(f)
                                                api_key = config.get('openai', {}).get('api_key')
                                        except:
                                            pass

                                    if not api_key:
                                        st.error("OpenAI API key not found. Please configure it in Streamlit secrets, environment, or config file.")
                                    else:
                                        client = OpenAI(api_key=api_key)

                                        # Build messages for API call
                                        messages = [
                                            {
                                                "role": "system",
                                                "content": f"""You are a helpful financial advisor assistant. You have access to the following analysis data for {ticker}:

{st.session_state[context_key]}

Use this information to answer the user's questions. Provide thoughtful, balanced advice considering both opportunities and risks. When discussing buy/hold/sell decisions, always remind the user to consider their own risk tolerance, investment timeline, and financial situation."""
                                            }
                                        ]

                                        # Add conversation history
                                        for msg in st.session_state.ai_conversation_history:
                                            messages.append({"role": msg["role"], "content": msg["content"]})

                                        # Add current question
                                        messages.append({"role": "user", "content": user_question})

                                        # Call OpenAI API
                                        response = client.chat.completions.create(
                                            model=model if model else "gpt-4o-mini",
                                            messages=messages,
                                            temperature=0.7,
                                            max_tokens=1000
                                        )

                                        ai_response = response.choices[0].message.content

                                        # Update conversation history
                                        st.session_state.ai_conversation_history.append({
                                            "role": "user",
                                            "content": user_question
                                        })
                                        st.session_state.ai_conversation_history.append({
                                            "role": "assistant",
                                            "content": ai_response
                                        })

                                        # Display the response
                                        st.markdown("**AI Response:**")
                                        st.info(ai_response)

                                except Exception as e:
                                    st.error(f"Error calling AI: {e}")
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

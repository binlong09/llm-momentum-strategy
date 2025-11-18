"""
Market Context Analysis
Analyzes overall market conditions, benchmarks, and regime detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import yfinance as yf
from loguru import logger


# Benchmark symbols
BENCHMARKS = {
    'SPY': 'S&P 500',
    'QQQ': 'Nasdaq 100',
    'DIA': 'Dow Jones',
    'IWM': 'Russell 2000',
    'VIX': 'Volatility Index'
}


def fetch_benchmark_data(
    symbols: List[str] = None,
    period: str = "1y"
) -> Dict[str, pd.DataFrame]:
    """
    Fetch benchmark price data.

    Args:
        symbols: List of benchmark symbols (defaults to all BENCHMARKS)
        period: Time period to fetch

    Returns:
        Dict mapping symbols to price DataFrames
    """
    if symbols is None:
        symbols = list(BENCHMARKS.keys())

    data = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)

            if not df.empty:
                data[symbol] = df
                logger.debug(f"Fetched {len(df)} days for {symbol}")
            else:
                logger.warning(f"No data for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")

    return data


def calculate_benchmark_returns(
    benchmark_data: Dict[str, pd.DataFrame],
    periods: List[int] = [1, 5, 21, 63, 126, 252]
) -> pd.DataFrame:
    """
    Calculate returns for benchmarks over multiple periods.

    Args:
        benchmark_data: Dict of benchmark price DataFrames
        periods: List of periods in days

    Returns:
        DataFrame with returns for each benchmark and period
    """
    results = []

    period_labels = {
        1: '1D',
        5: '1W',
        21: '1M',
        63: '3M',
        126: '6M',
        252: '1Y'
    }

    for symbol, df in benchmark_data.items():
        if df.empty:
            logger.warning(f"Empty data for {symbol}")
            continue

        # Need at least 1 day of data
        if len(df) < 1:
            continue

        row = {
            'symbol': symbol,
            'name': BENCHMARKS.get(symbol, symbol),
            'current_price': df['Close'].iloc[-1]
        }

        # Calculate returns for available periods
        has_data = False
        for period in periods:
            if len(df) >= period:
                start_price = df['Close'].iloc[-period]
                end_price = df['Close'].iloc[-1]
                ret = ((end_price / start_price) - 1) * 100

                label = period_labels.get(period, f'{period}D')
                row[label] = ret
                has_data = True

        # Only include if we got at least one period of data
        if has_data:
            results.append(row)
        else:
            logger.warning(f"Insufficient data for {symbol} (only {len(df)} days)")

    return pd.DataFrame(results)


def calculate_technical_signals(df: pd.DataFrame) -> Dict:
    """
    Calculate technical signals for a benchmark.

    Args:
        df: Price DataFrame with 'Close' column

    Returns:
        Dict with technical indicators
    """
    if df.empty or len(df) < 200:
        return {}

    close = df['Close']

    # Moving averages
    ma_20 = close.rolling(20).mean().iloc[-1]
    ma_50 = close.rolling(50).mean().iloc[-1]
    ma_200 = close.rolling(200).mean().iloc[-1]
    current = close.iloc[-1]

    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]

    # Trend determination
    if current > ma_50 and ma_50 > ma_200:
        trend = 'Bullish'
    elif current < ma_50 and ma_50 < ma_200:
        trend = 'Bearish'
    else:
        trend = 'Neutral'

    # Position relative to MAs
    above_50 = current > ma_50
    above_200 = current > ma_200

    return {
        'rsi': current_rsi,
        'ma_20': ma_20,
        'ma_50': ma_50,
        'ma_200': ma_200,
        'current_price': current,
        'above_50': above_50,
        'above_200': above_200,
        'trend': trend
    }


def detect_market_regime(benchmark_data: Dict[str, pd.DataFrame]) -> Dict:
    """
    Detect overall market regime (bull, bear, neutral).

    Args:
        benchmark_data: Dict of benchmark price DataFrames

    Returns:
        Dict with regime information
    """
    # Focus on S&P 500 as primary indicator
    spy_data = benchmark_data.get('SPY')
    vix_data = benchmark_data.get('VIX')

    if spy_data is None or spy_data.empty:
        return {'regime': 'Unknown', 'confidence': 0}

    # Calculate SPY technicals
    spy_tech = calculate_technical_signals(spy_data)

    # Get VIX level
    vix_level = vix_data['Close'].iloc[-1] if vix_data is not None and not vix_data.empty else None

    # Calculate market breadth (simplified)
    bullish_signals = 0
    total_signals = 0

    for symbol in ['SPY', 'QQQ', 'DIA', 'IWM']:
        if symbol in benchmark_data:
            tech = calculate_technical_signals(benchmark_data[symbol])
            if tech:
                total_signals += 2
                if tech['above_50']:
                    bullish_signals += 1
                if tech['above_200']:
                    bullish_signals += 1

    breadth_pct = (bullish_signals / total_signals * 100) if total_signals > 0 else 50

    # Determine regime
    if spy_tech['above_50'] and spy_tech['above_200'] and breadth_pct > 60:
        regime = 'Bull Market'
        confidence = min(100, int(breadth_pct + 20))
    elif not spy_tech['above_50'] and not spy_tech['above_200'] and breadth_pct < 40:
        regime = 'Bear Market'
        confidence = min(100, int((100 - breadth_pct) + 20))
    else:
        regime = 'Neutral'
        confidence = 60

    # VIX interpretation
    if vix_level:
        if vix_level < 15:
            fear_level = 'Low (Complacent)'
        elif vix_level < 20:
            fear_level = 'Normal'
        elif vix_level < 30:
            fear_level = 'Elevated'
        else:
            fear_level = 'High (Fear)'
    else:
        fear_level = 'Unknown'

    return {
        'regime': regime,
        'confidence': confidence,
        'breadth_pct': breadth_pct,
        'spy_above_50': spy_tech.get('above_50', False),
        'spy_above_200': spy_tech.get('above_200', False),
        'spy_rsi': spy_tech.get('rsi', 50),
        'spy_trend': spy_tech.get('trend', 'Unknown'),
        'vix_level': vix_level,
        'fear_level': fear_level
    }


def compare_portfolio_to_market(
    portfolio_returns: Dict,
    benchmark_returns: pd.DataFrame
) -> Dict:
    """
    Compare portfolio performance to market benchmarks.

    Args:
        portfolio_returns: Dict with portfolio return data
        benchmark_returns: DataFrame with benchmark returns

    Returns:
        Dict with comparison metrics
    """
    # Check if benchmark_returns is valid
    if benchmark_returns is None or benchmark_returns.empty:
        return {'error': 'No benchmark data available'}

    if 'symbol' not in benchmark_returns.columns:
        return {'error': 'Invalid benchmark data format'}

    comparisons = []

    # Get S&P 500 as primary benchmark
    spy_row = benchmark_returns[benchmark_returns['symbol'] == 'SPY']

    if spy_row.empty:
        return {'error': 'No S&P 500 data available'}

    # Compare available periods
    periods = ['1D', '1W', '1M', '3M', '6M', '1Y']

    for period in periods:
        if period in portfolio_returns and period in spy_row.columns:
            portfolio_ret = portfolio_returns[period]
            spy_ret = spy_row[period].iloc[0]

            alpha = portfolio_ret - spy_ret

            if spy_ret != 0:
                relative_perf = (portfolio_ret / spy_ret) * 100
            else:
                relative_perf = None

            comparisons.append({
                'period': period,
                'portfolio': portfolio_ret,
                'spy': spy_ret,
                'alpha': alpha,
                'relative_perf': relative_perf,
                'beating_market': alpha > 0
            })

    return {
        'comparisons': comparisons,
        'overall_alpha': sum(c['alpha'] for c in comparisons) / len(comparisons) if comparisons else 0
    }


def calculate_portfolio_beta(
    portfolio_returns: pd.Series,
    market_returns: pd.Series
) -> Dict:
    """
    Calculate portfolio beta relative to market.

    Args:
        portfolio_returns: Series of portfolio daily returns
        market_returns: Series of market (SPY) daily returns

    Returns:
        Dict with beta and related metrics
    """
    # Align the series
    aligned = pd.concat([portfolio_returns, market_returns], axis=1, join='inner')
    aligned.columns = ['portfolio', 'market']
    aligned = aligned.dropna()

    if len(aligned) < 30:
        return {'error': 'Insufficient data for beta calculation'}

    # Calculate beta (covariance / variance)
    covariance = aligned['portfolio'].cov(aligned['market'])
    market_variance = aligned['market'].var()

    if market_variance == 0:
        return {'error': 'Market variance is zero'}

    beta = covariance / market_variance

    # Calculate correlation
    correlation = aligned['portfolio'].corr(aligned['market'])

    # Calculate alpha (Jensen's alpha)
    portfolio_mean = aligned['portfolio'].mean()
    market_mean = aligned['market'].mean()
    alpha = portfolio_mean - (beta * market_mean)

    # Interpret beta
    if beta > 1.2:
        interpretation = 'High Risk/High Reward (very volatile)'
    elif beta > 1.0:
        interpretation = 'Aggressive (more volatile than market)'
    elif beta > 0.8:
        interpretation = 'Moderate (similar to market)'
    elif beta > 0.5:
        interpretation = 'Conservative (less volatile)'
    else:
        interpretation = 'Defensive (low correlation to market)'

    return {
        'beta': beta,
        'alpha': alpha * 252,  # Annualized
        'correlation': correlation,
        'interpretation': interpretation,
        'num_observations': len(aligned)
    }


def generate_market_summary(
    regime: Dict,
    benchmark_returns: pd.DataFrame,
    portfolio_comparison: Optional[Dict] = None
) -> str:
    """
    Generate a text summary of market conditions.

    Args:
        regime: Market regime dict
        benchmark_returns: Benchmark returns DataFrame
        portfolio_comparison: Optional portfolio comparison

    Returns:
        Text summary
    """
    summary_parts = []

    # Market regime
    summary_parts.append(f"📊 Market Regime: {regime['regime']} (Confidence: {regime['confidence']}%)")
    summary_parts.append(f"   - S&P 500 Trend: {regime.get('spy_trend', 'Unknown')}")
    summary_parts.append(f"   - Market Breadth: {regime.get('breadth_pct', 0):.0f}% bullish")

    if regime.get('vix_level'):
        summary_parts.append(f"   - VIX (Fear Index): {regime['vix_level']:.1f} - {regime.get('fear_level', 'Unknown')}")

    # Benchmark performance
    summary_parts.append("\n📈 Benchmark Performance:")
    for _, row in benchmark_returns.iterrows():
        if row['symbol'] != 'VIX':
            period_1m = row.get('1M', 0)
            summary_parts.append(f"   - {row['name']}: {period_1m:+.1f}% (1M)")

    # Portfolio comparison
    if portfolio_comparison and 'comparisons' in portfolio_comparison:
        summary_parts.append("\n💼 Your Portfolio vs S&P 500:")
        for comp in portfolio_comparison['comparisons'][-3:]:  # Last 3 periods
            status = '✅' if comp['beating_market'] else '⚠️'
            summary_parts.append(
                f"   - {comp['period']}: {comp['portfolio']:+.1f}% vs {comp['spy']:+.1f}% "
                f"(Alpha: {comp['alpha']:+.1f}%) {status}"
            )

    return '\n'.join(summary_parts)


def get_market_context_for_llm(
    regime: Dict,
    benchmark_returns: pd.DataFrame
) -> str:
    """
    Generate market context summary for LLM prompts.

    Args:
        regime: Market regime dict
        benchmark_returns: Benchmark returns DataFrame

    Returns:
        Concise market context for LLM
    """
    spy_row = benchmark_returns[benchmark_returns['symbol'] == 'SPY']

    if spy_row.empty:
        return "Market context unavailable."

    spy_1m = spy_row['1M'].iloc[0] if '1M' in spy_row.columns else 0
    spy_3m = spy_row['3M'].iloc[0] if '3M' in spy_row.columns else 0

    context = f"""MARKET CONTEXT:
- Regime: {regime['regime']} (Confidence: {regime['confidence']}%)
- S&P 500 Trend: {regime.get('spy_trend', 'Unknown')} (RSI: {regime.get('spy_rsi', 50):.0f})
- S&P 500 Performance: {spy_1m:+.1f}% (1M), {spy_3m:+.1f}% (3M)
- Market Breadth: {regime.get('breadth_pct', 0):.0f}% of indices above key moving averages
- Fear Index (VIX): {regime.get('vix_level', 0):.1f} - {regime.get('fear_level', 'Unknown')}

INTERPRETATION: """

    if regime['regime'] == 'Bull Market':
        context += "Strong market environment favoring risk-on positions. Good time for momentum strategies."
    elif regime['regime'] == 'Bear Market':
        context += "Weak market environment. Consider defensive positions and capital preservation."
    else:
        context += "Mixed market signals. Be selective and focus on individual stock fundamentals."

    return context

"""
Technical Indicators for Momentum Analysis
Calculates RSI, momentum acceleration, volume analysis, and moving averages
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: Series of closing prices
        period: RSI period (default 14)

    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return None

    # Calculate price changes
    delta = prices.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Calculate average gains and losses
    avg_gains = gains.rolling(window=period).mean()
    avg_losses = losses.rolling(window=period).mean()

    # Calculate RS and RSI
    rs = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]


def calculate_momentum_acceleration(prices: pd.Series) -> Optional[Dict]:
    """
    Calculate momentum acceleration (week-over-week change).

    Args:
        prices: Series of closing prices

    Returns:
        Dict with momentum metrics
    """
    if len(prices) < 10:  # Need at least 2 weeks of data
        return None

    try:
        # Calculate weekly returns
        current_price = prices.iloc[-1]
        week_ago_price = prices.iloc[-6] if len(prices) >= 6 else prices.iloc[0]
        two_weeks_ago_price = prices.iloc[-11] if len(prices) >= 11 else prices.iloc[0]

        # Current week momentum
        current_week_return = (current_price / week_ago_price - 1) * 100

        # Previous week momentum
        prev_week_return = (week_ago_price / two_weeks_ago_price - 1) * 100

        # Acceleration (change in momentum)
        acceleration = current_week_return - prev_week_return

        # Classify
        if acceleration > 2:
            status = "ACCELERATING"
        elif acceleration < -2:
            status = "DECELERATING"
        else:
            status = "STABLE"

        return {
            'current_week_return': current_week_return,
            'prev_week_return': prev_week_return,
            'acceleration': acceleration,
            'status': status
        }
    except:
        return None


def analyze_volume(prices_df: pd.DataFrame, volume_col: str = 'volume') -> Optional[Dict]:
    """
    Analyze volume patterns and unusual activity.

    Args:
        prices_df: DataFrame with price and volume data
        volume_col: Name of volume column

    Returns:
        Dict with volume analysis
    """
    if volume_col not in prices_df.columns or len(prices_df) < 20:
        return None

    try:
        volume = prices_df[volume_col]

        # Current volume
        current_volume = volume.iloc[-1]

        # 20-day average volume
        avg_volume_20 = volume.tail(20).mean()

        # Volume ratio
        volume_ratio = current_volume / avg_volume_20

        # 5-day volume trend (increasing/decreasing)
        recent_volume = volume.tail(5).mean()
        prev_volume = volume.iloc[-10:-5].mean() if len(volume) >= 10 else avg_volume_20
        volume_trend_pct = ((recent_volume / prev_volume) - 1) * 100

        # Classify
        if volume_ratio > 2.0:
            activity = "VERY HIGH"
        elif volume_ratio > 1.5:
            activity = "HIGH"
        elif volume_ratio > 0.8:
            activity = "NORMAL"
        else:
            activity = "LOW"

        trend = "INCREASING" if volume_trend_pct > 20 else "DECREASING" if volume_trend_pct < -20 else "STABLE"

        return {
            'current_volume': current_volume,
            'avg_volume_20': avg_volume_20,
            'volume_ratio': volume_ratio,
            'volume_trend_pct': volume_trend_pct,
            'activity_level': activity,
            'trend': trend
        }
    except:
        return None


def calculate_moving_averages(prices: pd.Series) -> Optional[Dict]:
    """
    Calculate key moving averages and price positions.

    Args:
        prices: Series of closing prices

    Returns:
        Dict with MA analysis
    """
    if len(prices) < 50:
        return None

    try:
        current_price = prices.iloc[-1]

        # Calculate MAs
        ma_50 = prices.tail(50).mean() if len(prices) >= 50 else None
        ma_200 = prices.tail(200).mean() if len(prices) >= 200 else None

        result = {
            'current_price': current_price,
            'ma_50': ma_50,
            'ma_200': ma_200
        }

        # Price vs MAs
        if ma_50:
            pct_from_ma50 = ((current_price / ma_50) - 1) * 100
            result['pct_from_ma50'] = pct_from_ma50
            result['above_ma50'] = current_price > ma_50

        if ma_200:
            pct_from_ma200 = ((current_price / ma_200) - 1) * 100
            result['pct_from_ma200'] = pct_from_ma200
            result['above_ma200'] = current_price > ma_200

        # Golden Cross / Death Cross
        if ma_50 and ma_200:
            if ma_50 > ma_200:
                result['ma_cross'] = "GOLDEN_CROSS"  # Bullish
                result['trend'] = "UPTREND"
            else:
                result['ma_cross'] = "DEATH_CROSS"  # Bearish
                result['trend'] = "DOWNTREND"

        # Trend strength
        if ma_50 and ma_200:
            ma_spread = ((ma_50 / ma_200) - 1) * 100
            result['ma_spread'] = ma_spread

            if abs(ma_spread) > 5:
                result['trend_strength'] = "STRONG"
            elif abs(ma_spread) > 2:
                result['trend_strength'] = "MODERATE"
            else:
                result['trend_strength'] = "WEAK"

        return result
    except:
        return None


def analyze_stock_technicals(price_data: pd.DataFrame) -> Dict:
    """
    Comprehensive technical analysis for a stock.

    Args:
        price_data: DataFrame with OHLCV data

    Returns:
        Dict with all technical indicators
    """
    result = {}

    try:
        if 'adjusted_close' in price_data.columns:
            prices = price_data['adjusted_close']
        elif 'close' in price_data.columns:
            prices = price_data['close']
        else:
            return result

        # RSI
        rsi = calculate_rsi(prices)
        if rsi is not None:
            result['rsi'] = rsi
            if rsi > 70:
                result['rsi_signal'] = "OVERBOUGHT"
            elif rsi < 30:
                result['rsi_signal'] = "OVERSOLD"
            else:
                result['rsi_signal'] = "NEUTRAL"

        # Momentum Acceleration
        momentum = calculate_momentum_acceleration(prices)
        if momentum:
            result['momentum'] = momentum

        # Volume Analysis
        volume_analysis = analyze_volume(price_data)
        if volume_analysis:
            result['volume'] = volume_analysis

        # Moving Averages
        ma_analysis = calculate_moving_averages(prices)
        if ma_analysis:
            result['moving_averages'] = ma_analysis

        return result

    except Exception as e:
        return result

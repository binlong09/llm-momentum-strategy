"""
Sector Analysis for Portfolio Intelligence
Analyzes sector concentration, momentum, and rotation patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


# Sector mapping (you can extend this)
SECTOR_MAP = {
    # Technology
    'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'GOOG': 'Technology',
    'META': 'Technology', 'NVDA': 'Technology', 'AMD': 'Technology', 'INTC': 'Technology',
    'AVGO': 'Technology', 'ORCL': 'Technology', 'CSCO': 'Technology', 'ADBE': 'Technology',
    'CRM': 'Technology', 'QCOM': 'Technology', 'TXN': 'Technology', 'AMAT': 'Technology',

    # Communication Services
    'NFLX': 'Communication Services', 'DIS': 'Communication Services', 'CMCSA': 'Communication Services',
    'T': 'Communication Services', 'VZ': 'Communication Services', 'TMUS': 'Communication Services',

    # Consumer Discretionary
    'AMZN': 'Consumer Discretionary', 'TSLA': 'Consumer Discretionary', 'HD': 'Consumer Discretionary',
    'NKE': 'Consumer Discretionary', 'MCD': 'Consumer Discretionary', 'SBUX': 'Consumer Discretionary',
    'TGT': 'Consumer Discretionary', 'LOW': 'Consumer Discretionary',

    # Consumer Staples
    'PG': 'Consumer Staples', 'KO': 'Consumer Staples', 'PEP': 'Consumer Staples',
    'WMT': 'Consumer Staples', 'COST': 'Consumer Staples', 'CL': 'Consumer Staples',

    # Healthcare
    'UNH': 'Healthcare', 'JNJ': 'Healthcare', 'LLY': 'Healthcare', 'ABBV': 'Healthcare',
    'MRK': 'Healthcare', 'PFE': 'Healthcare', 'TMO': 'Healthcare', 'ABT': 'Healthcare',

    # Financials
    'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials', 'V': 'Financials',
    'MA': 'Financials', 'GS': 'Financials', 'MS': 'Financials', 'AXP': 'Financials',
    'BLK': 'Financials', 'SCHW': 'Financials',

    # Industrials
    'BA': 'Industrials', 'CAT': 'Industrials', 'GE': 'Industrials', 'UPS': 'Industrials',
    'HON': 'Industrials', 'UNP': 'Industrials', 'LMT': 'Industrials',

    # Energy
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',

    # Materials
    'LIN': 'Materials', 'APD': 'Materials', 'ECL': 'Materials',

    # Real Estate
    'AMT': 'Real Estate', 'PLD': 'Real Estate', 'CCI': 'Real Estate',

    # Utilities
    'NEE': 'Utilities', 'DUK': 'Utilities', 'SO': 'Utilities',

    # Crypto/Fintech
    'COIN': 'Financials', 'SQ': 'Financials', 'PYPL': 'Financials',
}


def get_sector(symbol: str) -> str:
    """
    Get sector for a stock symbol.

    Args:
        symbol: Stock ticker

    Returns:
        Sector name or 'Other'
    """
    return SECTOR_MAP.get(symbol, 'Other')


def analyze_sector_concentration(holdings_df: pd.DataFrame) -> Dict:
    """
    Analyze sector concentration in portfolio.

    Args:
        holdings_df: DataFrame with holdings (must have 'symbol' and 'current_weight' columns)

    Returns:
        Dict with sector concentration metrics
    """
    if 'symbol' not in holdings_df.columns or 'current_weight' not in holdings_df.columns:
        return {}

    # Add sectors to holdings
    holdings_df = holdings_df.copy()
    holdings_df['sector'] = holdings_df['symbol'].apply(get_sector)

    # Calculate sector weights
    sector_weights = holdings_df.groupby('sector')['current_weight'].sum() * 100
    sector_weights = sector_weights.sort_values(ascending=False)

    # Concentration metrics
    top_sector = sector_weights.iloc[0] if len(sector_weights) > 0 else 0
    top_sector_name = sector_weights.index[0] if len(sector_weights) > 0 else 'None'

    top_3_sectors = sector_weights.head(3).sum() if len(sector_weights) >= 3 else sector_weights.sum()

    # Diversification score (inverse of concentration)
    # Perfect diversification (11 sectors equally weighted) = 100
    # All in one sector = 0
    num_sectors = len(sector_weights[sector_weights > 1])  # Sectors with >1% weight
    herfindahl_index = (sector_weights / 100) ** 2
    herfindahl_sum = herfindahl_index.sum()
    diversification_score = max(0, min(100, (1 - herfindahl_sum) * 100 / 0.9))  # Normalized

    return {
        'sector_weights': sector_weights.to_dict(),
        'top_sector': top_sector_name,
        'top_sector_weight': top_sector,
        'top_3_sectors_weight': top_3_sectors,
        'num_sectors': num_sectors,
        'diversification_score': diversification_score,
        'concentration_level': 'HIGH' if top_sector > 40 else 'MEDIUM' if top_sector > 25 else 'LOW'
    }


def analyze_sector_momentum(holdings_df: pd.DataFrame, price_data: Dict) -> Dict:
    """
    Analyze momentum by sector.

    Args:
        holdings_df: DataFrame with holdings
        price_data: Dict of price DataFrames by symbol

    Returns:
        Dict with sector momentum metrics
    """
    if 'symbol' not in holdings_df.columns:
        return {}

    sector_returns = defaultdict(list)
    sector_weights = defaultdict(float)

    for _, row in holdings_df.iterrows():
        symbol = row['symbol']
        sector = get_sector(symbol)
        weight = row.get('current_weight', 0)

        # Calculate stock momentum
        if symbol in price_data and not price_data[symbol].empty:
            prices = price_data[symbol]['adjusted_close'] if 'adjusted_close' in price_data[symbol].columns else price_data[symbol]['close']

            if len(prices) >= 21:  # 1 month
                month_return = (prices.iloc[-1] / prices.iloc[-21] - 1) * 100
                sector_returns[sector].append(month_return)
                sector_weights[sector] += weight

    # Calculate weighted sector momentum
    sector_momentum = {}
    for sector in sector_returns:
        if sector_returns[sector]:
            # Average momentum in sector
            avg_momentum = np.mean(sector_returns[sector])
            sector_momentum[sector] = {
                'momentum': avg_momentum,
                'weight': sector_weights[sector] * 100,
                'num_stocks': len(sector_returns[sector])
            }

    # Sort by momentum
    sorted_sectors = sorted(sector_momentum.items(), key=lambda x: x[1]['momentum'], reverse=True)

    return {
        'sector_momentum': dict(sorted_sectors),
        'leading_sector': sorted_sectors[0][0] if sorted_sectors else None,
        'lagging_sector': sorted_sectors[-1][0] if sorted_sectors else None,
        'momentum_spread': sorted_sectors[0][1]['momentum'] - sorted_sectors[-1][1]['momentum'] if len(sorted_sectors) >= 2 else 0
    }


def detect_sector_rotation(current_momentum: Dict, previous_momentum: Optional[Dict] = None) -> Dict:
    """
    Detect sector rotation patterns.

    Args:
        current_momentum: Current sector momentum dict
        previous_momentum: Previous period sector momentum (optional)

    Returns:
        Dict with rotation signals
    """
    if not current_momentum or 'sector_momentum' not in current_momentum:
        return {}

    sector_mom = current_momentum['sector_momentum']

    # Classify sectors
    gaining_sectors = []
    fading_sectors = []

    for sector, data in sector_mom.items():
        momentum = data['momentum']
        if momentum > 5:
            gaining_sectors.append((sector, momentum))
        elif momentum < -5:
            fading_sectors.append((sector, momentum))

    # Detect rotation if we have previous data
    rotation_detected = False
    rotation_description = ""

    if previous_momentum and 'sector_momentum' in previous_momentum:
        prev_mom = previous_momentum['sector_momentum']

        # Check if leadership changed
        prev_leader = max(prev_mom.items(), key=lambda x: x[1]['momentum'])[0] if prev_mom else None
        curr_leader = current_momentum.get('leading_sector')

        if prev_leader and curr_leader and prev_leader != curr_leader:
            rotation_detected = True
            rotation_description = f"Rotation from {prev_leader} to {curr_leader}"

    return {
        'gaining_sectors': sorted(gaining_sectors, key=lambda x: x[1], reverse=True),
        'fading_sectors': sorted(fading_sectors, key=lambda x: x[1]),
        'rotation_detected': rotation_detected,
        'rotation_description': rotation_description,
        'num_gaining': len(gaining_sectors),
        'num_fading': len(fading_sectors)
    }


def generate_sector_recommendations(concentration: Dict, momentum: Dict, rotation: Dict) -> List[str]:
    """
    Generate actionable sector recommendations.

    Args:
        concentration: Sector concentration analysis
        momentum: Sector momentum analysis
        rotation: Sector rotation detection

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Concentration warnings
    if concentration.get('concentration_level') == 'HIGH':
        top_sector = concentration.get('top_sector')
        top_weight = concentration.get('top_sector_weight', 0)
        recommendations.append(
            f"⚠️ HIGH CONCENTRATION: {top_weight:.1f}% in {top_sector} - Consider diversifying"
        )

    # Momentum warnings
    if momentum and 'sector_momentum' in momentum:
        sector_mom = momentum['sector_momentum']

        # Check if you're heavy in lagging sectors
        lagging = momentum.get('lagging_sector')
        if lagging and lagging in sector_mom:
            lagging_weight = sector_mom[lagging].get('weight', 0)
            lagging_momentum = sector_mom[lagging].get('momentum', 0)
            if lagging_weight > 20 and lagging_momentum < -5:
                recommendations.append(
                    f"📉 LAGGING EXPOSURE: {lagging_weight:.1f}% in {lagging} (momentum {lagging_momentum:+.1f}%)"
                )

    # Rotation opportunities
    if rotation.get('rotation_detected'):
        recommendations.append(
            f"🔄 SECTOR ROTATION: {rotation.get('rotation_description')}"
        )

    # Diversification
    if concentration.get('diversification_score', 0) < 50:
        recommendations.append(
            f"💡 LOW DIVERSIFICATION: Score {concentration.get('diversification_score', 0):.0f}/100 - Spread across more sectors"
        )

    # All clear
    if not recommendations:
        recommendations.append("✅ Sector allocation looks healthy")

    return recommendations

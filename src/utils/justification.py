"""
Stock Ranking Justification Generator

Generates human-readable explanations for why each stock is ranked where it is.
"""

import pandas as pd
from typing import Dict


def generate_stock_justification(stock_row: pd.Series, rank: int, total_stocks: int) -> Dict[str, str]:
    """
    Generate detailed justification for a stock's ranking.

    Args:
        stock_row: Series containing stock data
        rank: Stock's rank (1-indexed)
        total_stocks: Total number of stocks in portfolio

    Returns:
        Dictionary with justification details
    """
    symbol = stock_row['symbol']
    weight = stock_row.get('weight', 0)
    momentum_return = stock_row.get('momentum_return', 0)
    llm_score = stock_row.get('llm_score', None)
    risk_score = stock_row.get('risk_score', None)

    # Build justification components
    components = []

    # 1. Rank explanation
    percentile = ((total_stocks - rank) / total_stocks) * 100
    if rank <= 5:
        rank_desc = f"🏆 TOP 5 POSITION (#{rank}/{total_stocks})"
    elif rank <= 10:
        rank_desc = f"⭐ TOP 10 POSITION (#{rank}/{total_stocks})"
    elif percentile >= 75:
        rank_desc = f"✓ TOP 25% (#{rank}/{total_stocks})"
    elif percentile >= 50:
        rank_desc = f"○ TOP 50% (#{rank}/{total_stocks})"
    else:
        rank_desc = f"· BOTTOM 50% (#{rank}/{total_stocks})"

    # 2. Momentum explanation
    if momentum_return > 0.80:
        momentum_desc = f"🚀 **Exceptional** momentum: +{momentum_return*100:.1f}% (12 months)"
        momentum_rating = "Excellent"
    elif momentum_return > 0.50:
        momentum_desc = f"📈 **Strong** momentum: +{momentum_return*100:.1f}% (12 months)"
        momentum_rating = "Good"
    elif momentum_return > 0.30:
        momentum_desc = f"↗️ **Good** momentum: +{momentum_return*100:.1f}% (12 months)"
        momentum_rating = "Moderate"
    else:
        momentum_desc = f"→ **Moderate** momentum: +{momentum_return*100:.1f}% (12 months)"
        momentum_rating = "Fair"

    components.append(momentum_desc)

    # 3. LLM score explanation
    if llm_score is not None:
        if llm_score >= 0.9:
            llm_desc = f"🤖 **Very Bullish** AI assessment: {llm_score:.3f}/1.000"
            llm_detail = "News strongly suggests momentum will continue"
            llm_rating = "Very Bullish"
        elif llm_score >= 0.7:
            llm_desc = f"🤖 **Bullish** AI assessment: {llm_score:.3f}/1.000"
            llm_detail = "News indicates likely momentum continuation"
            llm_rating = "Bullish"
        elif llm_score >= 0.5:
            llm_desc = f"🤖 **Neutral** AI assessment: {llm_score:.3f}/1.000"
            llm_detail = "News shows mixed signals for momentum"
            llm_rating = "Neutral"
        elif llm_score >= 0.3:
            llm_desc = f"🤖 **Cautious** AI assessment: {llm_score:.3f}/1.000"
            llm_detail = "News suggests potential momentum slowdown"
            llm_rating = "Cautious"
        else:
            llm_desc = f"🤖 **Bearish** AI assessment: {llm_score:.3f}/1.000"
            llm_detail = "News indicates momentum may not continue"
            llm_rating = "Bearish"

        components.append(llm_desc)
        components.append(f"  → {llm_detail}")
    else:
        llm_rating = "N/A"

    # 4. Risk score explanation
    if risk_score is not None:
        key_risk = stock_row.get('key_risk', 'None identified')

        if risk_score < 0.4:
            risk_desc = f"🟢 **Low Risk**: {risk_score:.2f}/1.00"
            risk_detail = f"No significant concerns. {key_risk}"
            risk_rating = "Low"
        elif risk_score < 0.7:
            risk_desc = f"🟡 **Medium Risk**: {risk_score:.2f}/1.00"
            risk_detail = f"Some concerns to monitor. {key_risk}"
            risk_rating = "Medium"
        else:
            risk_desc = f"🔴 **High Risk**: {risk_score:.2f}/1.00"
            risk_detail = f"Significant concerns identified. {key_risk}"
            risk_rating = "High"

        components.append(risk_desc)
        components.append(f"  → {risk_detail}")

        # Risk breakdown if available
        risk_categories = {
            'financial_risk': ('💰', 'Financial'),
            'operational_risk': ('⚙️', 'Operational'),
            'regulatory_risk': ('⚖️', 'Regulatory'),
            'competitive_risk': ('🏁', 'Competitive'),
            'market_risk': ('📊', 'Market')
        }

        risk_breakdown = []
        for risk_type, (emoji, name) in risk_categories.items():
            if risk_type in stock_row.index:
                risk_level = stock_row[risk_type]
                # Color code the risk level
                if risk_level == "LOW":
                    indicator = "🟢"
                elif risk_level == "MEDIUM":
                    indicator = "🟡"
                else:
                    indicator = "🔴"

                risk_breakdown.append(f"{emoji} {name}: {indicator} {risk_level}")

        if risk_breakdown:
            components.append(f"  → Breakdown: {', '.join(risk_breakdown)}")
            components.append(f"  → 💰 Financial=earnings/debt, ⚙️ Operational=supply/production, ⚖️ Regulatory=legal/compliance, 🏁 Competitive=market share, 📊 Market=sector trends")
    else:
        risk_rating = "N/A"

    # 5. Weight explanation
    original_weight = stock_row.get('original_weight', weight)
    weight_change = weight - original_weight

    if abs(weight_change) > 0.01:
        if weight_change > 0:
            weight_desc = f"💼 Position **increased** to {weight*100:.2f}% (from {original_weight*100:.2f}%)"
        else:
            weight_desc = f"💼 Position **reduced** to {weight*100:.2f}% (from {original_weight*100:.2f}%)"

        # Explain why
        reasons = []
        if llm_score is not None and llm_score >= 0.9:
            reasons.append("high AI score")
        if risk_score is not None and risk_score >= 0.7:
            reasons.append("high risk")
        if risk_score is not None and risk_score < 0.4:
            reasons.append("low risk")

        if 'protection_type' in stock_row.index and stock_row['protection_type'] == 'Risk-Weighted':
            if risk_score is not None and risk_score >= 0.7:
                reasons.append("market volatility + high stock risk")
            elif risk_score is not None and risk_score < 0.4:
                reasons.append("market volatility only (low stock risk)")

        if reasons:
            weight_desc += f"\n  → Reason: {', '.join(reasons)}"

        components.append(weight_desc)
    else:
        components.append(f"💼 Portfolio weight: {weight*100:.2f}%")

    # 6. Overall summary
    if rank <= 5:
        summary = "**Top holding** - Strong across all metrics"
    elif llm_score and llm_score >= 0.9 and risk_score and risk_score < 0.4:
        summary = "**High conviction** - Great momentum, bullish AI, low risk"
    elif risk_score and risk_score >= 0.7:
        summary = "**Watch closely** - Good momentum but elevated risks"
    elif llm_score and llm_score < 0.5:
        summary = "**Lower conviction** - Momentum present but AI cautious"
    else:
        summary = "**Solid holding** - Meets criteria across key metrics"

    # Build final justification text
    justification = "\n\n".join(components)

    return {
        'rank': rank,
        'symbol': symbol,
        'rank_description': rank_desc,
        'summary': summary,
        'justification': justification,
        'momentum_rating': momentum_rating,
        'llm_rating': llm_rating,
        'risk_rating': risk_rating,
        'percentile': percentile
    }


def add_ranking_explanations(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Add ranking explanation column to portfolio.

    Args:
        portfolio: Portfolio DataFrame (assumed to be sorted by weight descending)

    Returns:
        Portfolio with 'ranking_explanation' column added
    """
    total_stocks = len(portfolio)
    explanations = []

    for rank, (idx, row) in enumerate(portfolio.iterrows(), start=1):
        just = generate_stock_justification(row, rank, total_stocks)
        explanations.append(just['summary'])

    portfolio_with_explanations = portfolio.copy()
    portfolio_with_explanations['ranking_explanation'] = explanations

    return portfolio_with_explanations


def generate_portfolio_summary(portfolio: pd.DataFrame) -> str:
    """
    Generate overall portfolio summary.

    Args:
        portfolio: Portfolio DataFrame

    Returns:
        Summary text
    """
    num_stocks = len(portfolio)

    # Count by ratings
    if 'risk_score' in portfolio.columns:
        low_risk = (portfolio['risk_score'] < 0.4).sum()
        medium_risk = ((portfolio['risk_score'] >= 0.4) & (portfolio['risk_score'] < 0.7)).sum()
        high_risk = (portfolio['risk_score'] >= 0.7).sum()

        risk_summary = f"""
**Risk Profile**:
- 🟢 {low_risk} low-risk stocks ({low_risk/num_stocks*100:.0f}%)
- 🟡 {medium_risk} medium-risk stocks ({medium_risk/num_stocks*100:.0f}%)
- 🔴 {high_risk} high-risk stocks ({high_risk/num_stocks*100:.0f}%)
"""
    else:
        risk_summary = ""

    if 'llm_score' in portfolio.columns:
        bullish = (portfolio['llm_score'] >= 0.7).sum()
        neutral = ((portfolio['llm_score'] >= 0.3) & (portfolio['llm_score'] < 0.7)).sum()
        bearish = (portfolio['llm_score'] < 0.3).sum()

        llm_summary = f"""
**AI Sentiment**:
- 🤖 {bullish} bullish ({bullish/num_stocks*100:.0f}%)
- 🤖 {neutral} neutral ({neutral/num_stocks*100:.0f}%)
- 🤖 {bearish} cautious ({bearish/num_stocks*100:.0f}%)
"""
    else:
        llm_summary = ""

    avg_momentum = portfolio['momentum_return'].mean() if 'momentum_return' in portfolio.columns else 0

    summary = f"""
**Portfolio Overview**: {num_stocks} stocks selected

**Average Momentum**: {avg_momentum*100:.1f}% (12-month)
{llm_summary}{risk_summary}
"""

    return summary.strip()

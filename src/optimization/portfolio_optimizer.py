"""
AI Portfolio Optimizer
Analyzes all available signals and provides definitive rebalancing recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PortfolioOptimizer:
    """
    AI-powered portfolio optimizer that aggregates all signals
    and provides clear rebalancing recommendations.
    """

    def __init__(self):
        self.recommendation = None
        self.confidence = 0
        self.reasoning = []
        self.stock_actions = {}

    def analyze_all_signals(
        self,
        market_signals: Optional[Dict] = None,
        portfolio_metrics: Optional[Dict] = None,
        technical_signals: Optional[Dict] = None,
        sector_analysis: Optional[Dict] = None,
        batch_analysis: Optional[Dict] = None,
        holdings_df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Comprehensive analysis of all available signals.

        Returns:
            Dict with recommendation, confidence, and reasoning
        """
        # Score each signal category
        scores = {
            'market': self._score_market_signals(market_signals),
            'portfolio': self._score_portfolio_metrics(portfolio_metrics),
            'technical': self._score_technical_signals(technical_signals),
            'sector': self._score_sector_analysis(sector_analysis),
            'ai_batch': self._score_batch_analysis(batch_analysis)
        }

        # Calculate overall score
        overall_score = self._calculate_overall_score(scores)

        # Generate recommendation
        recommendation, confidence = self._generate_recommendation(overall_score, scores)

        # Generate reasoning
        reasoning = self._generate_reasoning(scores, overall_score)

        # Stock-level actions
        stock_actions = self._generate_stock_actions(
            technical_signals,
            sector_analysis,
            batch_analysis,
            holdings_df
        )

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'overall_score': overall_score,
            'category_scores': scores,
            'reasoning': reasoning,
            'stock_actions': stock_actions,
            'timestamp': datetime.now().isoformat()
        }

    def _score_market_signals(self, signals: Optional[Dict]) -> Dict:
        """Score market-level signals (VIX, regime, SPY, etc.)"""
        if not signals:
            return {'score': 0, 'weight': 0.15, 'details': 'No market data'}

        score = 50  # Neutral
        details = []

        # Market regime scoring (new!)
        regime = signals.get('regime')
        regime_confidence = signals.get('regime_confidence', 0)

        if regime:
            if regime == 'Bull Market':
                score += 15
                details.append(f"Bull Market detected ({regime_confidence}% confidence)")
            elif regime == 'Bear Market':
                score -= 20
                details.append(f"Bear Market detected ({regime_confidence}% confidence) - defensive posture")
            else:  # Neutral
                score -= 5
                details.append(f"Neutral market - mixed signals")

        # Market breadth
        breadth = signals.get('breadth_pct')
        if breadth is not None:
            if breadth > 70:
                score += 5
                details.append(f"Strong breadth ({breadth:.0f}%)")
            elif breadth < 40:
                score -= 10
                details.append(f"Weak breadth ({breadth:.0f}%) - most stocks declining")

        # SPY position relative to MAs
        spy_above_50 = signals.get('spy_above_50')
        spy_above_200 = signals.get('spy_above_200')

        if spy_above_200 is False:
            score -= 10
            details.append("SPY below 200-day MA - long-term bearish")
        elif spy_above_50 is False and spy_above_200 is True:
            score -= 5
            details.append("SPY below 50-day MA but above 200-day - short-term caution")

        # VIX scoring
        vix = signals.get('vix')
        if vix:
            if vix > 35:
                score -= 20
                details.append(f"VIX very high ({vix:.1f}) - extreme fear, possible capitulation")
            elif vix > 25:
                score -= 10
                details.append(f"VIX elevated ({vix:.1f}) - heightened volatility")
            elif vix < 15:
                score += 10
                details.append(f"VIX low ({vix:.1f}) - calm market conditions")
            elif vix < 12:
                score -= 5
                details.append(f"VIX very low ({vix:.1f}) - possible complacency risk")

        # SPY trend scoring (returns)
        spy_5d = signals.get('spy_5d_return')
        spy_20d = signals.get('spy_20d_return')

        if spy_20d is not None:
            if spy_20d < -10:
                score -= 15
                details.append(f"SPY 1M: {spy_20d:+.1f}% - medium-term downtrend")
            elif spy_20d > 10:
                score += 10
                details.append(f"SPY 1M: {spy_20d:+.1f}% - strong uptrend")

        if spy_5d is not None:
            if spy_5d < -5:
                score -= 5
                details.append(f"SPY 1W: {spy_5d:+.1f}% - short-term pullback")

        return {
            'score': max(0, min(100, score)),
            'weight': 0.15,
            'details': '; '.join(details) if details else 'Market conditions normal'
        }

    def _score_portfolio_metrics(self, metrics: Optional[Dict]) -> Dict:
        """Score portfolio-level metrics"""
        if not metrics:
            return {'score': 0, 'weight': 0.20, 'details': 'No portfolio data'}

        score = 50  # Neutral
        details = []

        # Consecutive down days
        consecutive_down = metrics.get('consecutive_down', 0)
        if consecutive_down >= 5:
            score -= 20
            details.append(f"{consecutive_down} consecutive down days - concerning trend")
        elif consecutive_down >= 3:
            score -= 10
            details.append(f"{consecutive_down} consecutive down days - monitor closely")

        # Concentration risk
        top3_weight = metrics.get('top3_concentration', 0)
        if top3_weight > 60:
            score -= 15
            details.append(f"Top 3: {top3_weight:.1f}% - very high concentration")
        elif top3_weight > 50:
            score -= 10
            details.append(f"Top 3: {top3_weight:.1f}% - high concentration")

        # Time in portfolio
        days_in_portfolio = metrics.get('days_in_portfolio', 30)
        if days_in_portfolio < 7:
            score += 15
            details.append(f"Only {days_in_portfolio} days in - too early to judge")

        return {
            'score': max(0, min(100, score)),
            'weight': 0.20,
            'details': '; '.join(details) if details else 'Portfolio metrics healthy'
        }

    def _score_technical_signals(self, signals: Optional[Dict]) -> Dict:
        """Score technical indicators"""
        if not signals:
            return {'score': 0, 'weight': 0.25, 'details': 'No technical data'}

        score = 50  # Neutral
        details = []

        # Death crosses (very bearish)
        death_crosses = signals.get('death_crosses', [])
        if len(death_crosses) >= 2:
            score -= 30
            details.append(f"{len(death_crosses)} death crosses - major bearish signal")
        elif len(death_crosses) == 1:
            score -= 15
            details.append(f"1 death cross - bearish signal")

        # Decelerating momentum
        decelerating = signals.get('decelerating', [])
        if len(decelerating) >= 4:
            score -= 15
            details.append(f"{len(decelerating)} stocks decelerating - momentum fading")
        elif len(decelerating) >= 2:
            score -= 8
            details.append(f"{len(decelerating)} stocks decelerating - watch closely")

        # Overbought (neutral to slightly negative)
        overbought = signals.get('overbought', [])
        if len(overbought) >= 3:
            score -= 5
            details.append(f"{len(overbought)} stocks overbought - pullback risk")

        # Golden crosses (bullish)
        golden_crosses = signals.get('golden_crosses', [])
        if len(golden_crosses) >= 3:
            score += 15
            details.append(f"{len(golden_crosses)} golden crosses - strong trends")

        # Accelerating momentum (bullish)
        accelerating = signals.get('accelerating', [])
        if len(accelerating) >= 3:
            score += 10
            details.append(f"{len(accelerating)} stocks accelerating - strengthening")

        return {
            'score': max(0, min(100, score)),
            'weight': 0.25,
            'details': '; '.join(details) if details else 'Technical indicators neutral'
        }

    def _score_sector_analysis(self, analysis: Optional[Dict]) -> Dict:
        """Score sector concentration and rotation"""
        if not analysis:
            return {'score': 0, 'weight': 0.15, 'details': 'No sector data'}

        score = 50  # Neutral
        details = []

        concentration = analysis.get('concentration', {})

        # Concentration risk
        top_sector_weight = concentration.get('top_sector_weight', 0)
        if top_sector_weight > 60:
            score -= 20
            details.append(f"Extreme concentration: {top_sector_weight:.1f}% in one sector")
        elif top_sector_weight > 45:
            score -= 10
            details.append(f"High concentration: {top_sector_weight:.1f}% in {concentration.get('top_sector')}")

        # Diversification score
        div_score = concentration.get('diversification_score', 50)
        if div_score < 40:
            score -= 10
            details.append(f"Low diversification ({div_score:.0f}/100)")
        elif div_score > 70:
            score += 5
            details.append(f"Good diversification ({div_score:.0f}/100)")

        # Sector rotation
        rotation = analysis.get('rotation', {})
        if rotation.get('rotation_detected'):
            score -= 10
            details.append(f"Rotation detected: {rotation.get('rotation_description')}")

        return {
            'score': max(0, min(100, score)),
            'weight': 0.15,
            'details': '; '.join(details) if details else 'Sector allocation healthy'
        }

    def _score_batch_analysis(self, analysis: Optional[Dict]) -> Dict:
        """Score AI batch analysis results"""
        if not analysis:
            return {'score': 0, 'weight': 0.25, 'details': 'No AI analysis data'}

        score = 50  # Neutral
        details = []

        # Average sentiment
        avg_sentiment = analysis.get('avg_sentiment')
        if avg_sentiment is not None:
            if avg_sentiment < 0.4:
                score -= 20
                details.append(f"Portfolio bearish (sentiment {avg_sentiment:.2f})")
            elif avg_sentiment < 0.5:
                score -= 10
                details.append(f"Portfolio cautious (sentiment {avg_sentiment:.2f})")
            elif avg_sentiment > 0.7:
                score += 15
                details.append(f"Portfolio bullish (sentiment {avg_sentiment:.2f})")

        # Average risk
        avg_risk = analysis.get('avg_risk')
        if avg_risk is not None:
            if avg_risk > 0.7:
                score -= 20
                details.append(f"High portfolio risk ({avg_risk:.2f})")
            elif avg_risk > 0.6:
                score -= 10
                details.append(f"Elevated risk ({avg_risk:.2f})")
            elif avg_risk < 0.4:
                score += 10
                details.append(f"Low risk ({avg_risk:.2f})")

        # High-risk stocks count
        high_risk_count = analysis.get('high_risk_count', 0)
        if high_risk_count >= 4:
            score -= 15
            details.append(f"{high_risk_count} high-risk stocks")
        elif high_risk_count >= 2:
            score -= 8
            details.append(f"{high_risk_count} high-risk stocks")

        # Bearish stocks count
        bearish_count = analysis.get('bearish_count', 0)
        if bearish_count >= 3:
            score -= 12
            details.append(f"{bearish_count} bearish stocks")

        return {
            'score': max(0, min(100, score)),
            'weight': 0.25,
            'details': '; '.join(details) if details else 'AI analysis looks healthy'
        }

    def _calculate_overall_score(self, scores: Dict) -> float:
        """Calculate weighted overall score"""
        weighted_sum = 0
        total_weight = 0

        for category, data in scores.items():
            if data['weight'] > 0:
                weighted_sum += data['score'] * data['weight']
                total_weight += data['weight']

        return weighted_sum / total_weight if total_weight > 0 else 50

    def _generate_recommendation(self, overall_score: float, scores: Dict) -> Tuple[str, int]:
        """
        Generate final recommendation and confidence.

        Returns:
            Tuple of (recommendation: str, confidence: int)
        """
        # Check for critical signals that override score
        tech_score = scores.get('technical', {}).get('score', 50)
        ai_score = scores.get('ai_batch', {}).get('score', 50)

        # CRITICAL: Multiple death crosses = immediate rebalance
        if tech_score < 30:
            return ("REBALANCE_NOW", 90)

        # CRITICAL: Very high AI risk
        if ai_score < 25:
            return ("REBALANCE_NOW", 85)

        # Score-based recommendations
        if overall_score < 35:
            confidence = int(100 - overall_score)  # Lower score = higher confidence to rebalance
            return ("REBALANCE_NOW", min(95, confidence))
        elif overall_score < 45:
            return ("CONSIDER_REBALANCING", 65)
        elif overall_score < 55:
            return ("MONITOR_CLOSELY", 60)
        elif overall_score < 65:
            return ("WAIT", 70)
        else:
            confidence = int(overall_score)  # Higher score = higher confidence to wait
            return ("WAIT", min(95, confidence))

    def _generate_reasoning(self, scores: Dict, overall_score: float) -> List[str]:
        """Generate human-readable reasoning"""
        reasoning = []

        reasoning.append(f"Overall Health Score: {overall_score:.1f}/100")
        reasoning.append("")

        # Break down each category
        for category, data in sorted(scores.items(), key=lambda x: x[1]['score']):
            score = data['score']
            weight = data['weight']
            details = data['details']

            emoji = "🔴" if score < 40 else "🟡" if score < 60 else "🟢"
            category_name = category.replace('_', ' ').title()

            reasoning.append(f"{emoji} **{category_name}** ({score:.0f}/100, weight {weight*100:.0f}%)")
            reasoning.append(f"   {details}")

        return reasoning

    def _generate_stock_actions(
        self,
        technical_signals: Optional[Dict],
        sector_analysis: Optional[Dict],
        batch_analysis: Optional[Dict],
        holdings_df: Optional[pd.DataFrame]
    ) -> Dict[str, Dict]:
        """
        Generate stock-specific action recommendations.

        Returns:
            Dict mapping symbol to action details
        """
        actions = {}

        if holdings_df is None or len(holdings_df) == 0:
            return actions

        # Analyze each stock
        for _, row in holdings_df.iterrows():
            symbol = row.get('symbol')
            if not symbol:
                continue

            action = self._determine_stock_action(
                symbol,
                technical_signals,
                sector_analysis,
                batch_analysis,
                row
            )

            if action:
                actions[symbol] = action

        return actions

    def _determine_stock_action(
        self,
        symbol: str,
        technical_signals: Optional[Dict],
        sector_analysis: Optional[Dict],
        batch_analysis: Optional[Dict],
        stock_row: pd.Series
    ) -> Optional[Dict]:
        """Determine action for a specific stock"""
        action_score = 50  # Neutral
        reasons = []

        # Check technical signals
        if technical_signals:
            if symbol in technical_signals.get('death_crosses', []):
                action_score -= 30
                reasons.append("Death cross (50MA < 200MA)")

            if symbol in technical_signals.get('decelerating', []):
                action_score -= 15
                reasons.append("Momentum decelerating")

            if symbol in technical_signals.get('overbought', []):
                action_score -= 10
                reasons.append("Overbought (RSI >70)")

            if symbol in technical_signals.get('accelerating', []):
                action_score += 10
                reasons.append("Momentum accelerating")

        # Check batch analysis
        if batch_analysis and 'results' in batch_analysis:
            stock_analysis = next((r for r in batch_analysis['results'] if r.get('symbol') == symbol), None)
            if stock_analysis:
                risk = stock_analysis.get('risk_score')
                sentiment = stock_analysis.get('sentiment_score')

                if risk and risk > 0.7:
                    action_score -= 20
                    reasons.append(f"High risk ({risk:.2f})")

                if sentiment and sentiment < 0.4:
                    action_score -= 15
                    reasons.append(f"Bearish sentiment ({sentiment:.2f})")

        # Determine action
        if action_score < 30:
            return {
                'action': 'EXIT',
                'priority': 'HIGH',
                'reasons': reasons,
                'confidence': 85
            }
        elif action_score < 45:
            return {
                'action': 'REDUCE',
                'priority': 'MEDIUM',
                'reasons': reasons,
                'confidence': 70
            }
        elif action_score < 55:
            return {
                'action': 'MONITOR',
                'priority': 'LOW',
                'reasons': reasons,
                'confidence': 60
            }
        elif action_score > 65:
            return {
                'action': 'HOLD',
                'priority': 'LOW',
                'reasons': ['Strong position'] if len(reasons) == 0 else reasons,
                'confidence': 75
            }

        return None  # No specific action needed

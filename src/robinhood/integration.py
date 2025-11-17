"""
Robinhood Integration (Read-Only)
Fetch current portfolio holdings from Robinhood API
NO TRADE EXECUTION - For portfolio comparison only
"""

import robin_stocks.robinhood as rh
import pandas as pd
from typing import Dict, Optional, Tuple
import os
from pathlib import Path


class RobinhoodPortfolioFetcher:
    """
    Fetch portfolio data from Robinhood.
    READ-ONLY: Does not execute any trades.
    """

    def __init__(self):
        """Initialize fetcher (not logged in yet)."""
        self.logged_in = False
        self.username = None

    def login(self, username: str, password: str, mfa_code: Optional[str] = None) -> Tuple[bool, str]:
        """
        Login to Robinhood.

        Args:
            username: Robinhood email/username
            password: Robinhood password
            mfa_code: 2FA code if enabled (6-digit code from authenticator app)

        Returns:
            (success: bool, message: str)
        """
        try:
            # Login with optional MFA
            if mfa_code:
                login_result = rh.login(username, password, mfa_code=mfa_code)
            else:
                login_result = rh.login(username, password)

            if login_result:
                self.logged_in = True
                self.username = username
                return True, "✅ Successfully logged in to Robinhood"
            else:
                return False, "❌ Login failed. Check credentials."

        except Exception as e:
            error_msg = str(e)
            if "MFA" in error_msg or "verification" in error_msg:
                return False, "❌ 2FA code required. Please provide MFA code."
            else:
                return False, f"❌ Login error: {error_msg}"

    def logout(self):
        """Logout from Robinhood."""
        rh.logout()
        self.logged_in = False
        self.username = None

    def get_portfolio_value(self) -> float:
        """
        Get total portfolio value.

        Returns:
            Total account value in dollars
        """
        if not self.logged_in:
            raise ValueError("Not logged in. Call login() first.")

        try:
            profile = rh.profiles.load_account_profile()
            equity = float(profile['equity'])
            return equity
        except Exception as e:
            raise ValueError(f"Error fetching portfolio value: {e}")

    def get_current_positions(self) -> pd.DataFrame:
        """
        Fetch current positions from Robinhood.

        Returns:
            DataFrame with columns: symbol, shares, avg_cost, current_price, market_value, weight
        """
        if not self.logged_in:
            raise ValueError("Not logged in. Call login() first.")

        try:
            # Get all positions
            positions = rh.account.build_holdings()

            if not positions:
                return pd.DataFrame()

            # Get total portfolio value
            total_value = self.get_portfolio_value()

            # Convert to DataFrame
            holdings_data = []

            for symbol, data in positions.items():
                shares = float(data['quantity'])
                avg_cost = float(data['average_buy_price'])
                current_price = float(data['price'])
                market_value = shares * current_price
                weight = market_value / total_value if total_value > 0 else 0

                holdings_data.append({
                    'symbol': symbol,
                    'shares': shares,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'market_value': market_value,
                    'weight': weight,
                    'pnl_dollar': market_value - (shares * avg_cost),
                    'pnl_percent': ((current_price - avg_cost) / avg_cost) if avg_cost > 0 else 0
                })

            df = pd.DataFrame(holdings_data)
            df = df.sort_values('market_value', ascending=False)

            return df

        except Exception as e:
            raise ValueError(f"Error fetching positions: {e}")

    def compare_with_target(
        self,
        target_portfolio: pd.DataFrame,
        current_positions: pd.DataFrame = None
    ) -> Dict:
        """
        Compare current Robinhood positions with target portfolio.

        Args:
            target_portfolio: DataFrame with 'symbol' and 'weight' columns
            current_positions: Optional. If None, fetches from Robinhood

        Returns:
            Dict with 'sells', 'buys', 'rebalances', 'summary'
        """
        # Fetch current positions if not provided
        if current_positions is None:
            current_positions = self.get_current_positions()

        total_value = current_positions['market_value'].sum()

        # Get symbol sets
        current_symbols = set(current_positions['symbol'].values)
        target_symbols = set(target_portfolio['symbol'].values)

        # Categorize trades
        sells = current_symbols - target_symbols
        buys = target_symbols - current_symbols
        holds = current_symbols & target_symbols

        # Calculate sell details
        sell_data = []
        for symbol in sorted(sells):
            pos = current_positions[current_positions['symbol'] == symbol].iloc[0]
            sell_data.append({
                'symbol': symbol,
                'current_value': pos['market_value'],
                'shares': pos['shares'],
                'action': 'SELL ALL',
                'instruction': f"Sell all {pos['shares']:.4f} shares"
            })

        # Calculate buy details
        buy_data = []
        for symbol in sorted(buys):
            target_row = target_portfolio[target_portfolio['symbol'] == symbol].iloc[0]
            target_value = target_row['weight'] * total_value
            target_weight = target_row['weight']

            buy_data.append({
                'symbol': symbol,
                'target_value': target_value,
                'target_weight': target_weight,
                'action': f'BUY ${target_value:.2f}',
                'instruction': f"Buy ${target_value:.2f} worth"
            })

        # Calculate rebalance details
        rebalance_data = []
        for symbol in sorted(holds):
            current_row = current_positions[current_positions['symbol'] == symbol].iloc[0]
            target_row = target_portfolio[target_portfolio['symbol'] == symbol].iloc[0]

            current_value = current_row['market_value']
            current_weight = current_row['weight']
            target_value = target_row['weight'] * total_value
            target_weight = target_row['weight']

            diff_value = target_value - current_value
            diff_weight = target_weight - current_weight

            # Only include if difference > 2%
            if abs(diff_weight) > 0.02:
                if diff_value > 0:
                    action = f"BUY ${abs(diff_value):.2f}"
                    instruction = f"Buy ${abs(diff_value):.2f} more"
                else:
                    action = f"SELL ${abs(diff_value):.2f}"
                    instruction = f"Sell ${abs(diff_value):.2f} worth"

                rebalance_data.append({
                    'symbol': symbol,
                    'current_value': current_value,
                    'current_weight': current_weight,
                    'target_value': target_value,
                    'target_weight': target_weight,
                    'diff_value': diff_value,
                    'diff_weight': diff_weight,
                    'action': action,
                    'instruction': instruction
                })

        # Summary
        turnover = (len(sells) + len(buys)) / max(len(current_symbols), 1) if current_symbols else 1.0

        return {
            'total_value': total_value,
            'sells': pd.DataFrame(sell_data) if sell_data else pd.DataFrame(),
            'buys': pd.DataFrame(buy_data) if buy_data else pd.DataFrame(),
            'rebalances': pd.DataFrame(rebalance_data) if rebalance_data else pd.DataFrame(),
            'summary': {
                'total_positions': len(target_portfolio),
                'current_positions': len(current_positions),
                'sells_count': len(sells),
                'buys_count': len(buys),
                'rebalances_count': len(rebalance_data),
                'turnover': turnover,
                'total_value': total_value
            }
        }


def save_credentials(username: str, device_token_path: str = ".robinhood_device_token"):
    """
    Save device token to avoid repeated MFA prompts.

    Args:
        username: Robinhood username
        device_token_path: Path to save device token
    """
    # Robin_stocks automatically saves device token after successful login
    # This is just a placeholder for documentation
    pass


def load_credentials(device_token_path: str = ".robinhood_device_token") -> bool:
    """
    Check if device token exists (allows login without MFA).

    Returns:
        True if token exists
    """
    return Path(device_token_path).exists()

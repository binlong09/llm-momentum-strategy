"""
Portfolio Tracker - Daily snapshots and historical tracking
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
import yfinance as yf
import os


def get_default_history_dir():
    """Get default history directory based on environment."""
    # Use persistent storage on Streamlit Cloud
    if os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud":
        # Streamlit Cloud provides /mount/data for persistence
        return "/mount/data/monitoring"
    return "results/monitoring"


class PortfolioTracker:
    """Track portfolio value and holdings over time."""

    def __init__(self, history_dir: str = None):
        if history_dir is None:
            history_dir = get_default_history_dir()

        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_file = self.history_dir / "portfolio_snapshots.csv"
        self.holdings_file = self.history_dir / "holdings_history.csv"
        self.market_context_file = self.history_dir / "market_context_history.csv"

    def snapshot_portfolio(
        self,
        holdings_df: pd.DataFrame,
        source: str = "manual",
        market_context: Optional[Dict] = None
    ) -> Dict:
        """
        Take a snapshot of current portfolio.

        Args:
            holdings_df: DataFrame with ['symbol', 'shares', 'current_price', 'current_value']
            source: Source of data ('manual', 'robinhood', 'auto')
            market_context: Optional market context data to save alongside snapshot

        Returns:
            Dictionary with snapshot data
        """
        timestamp = datetime.now()

        # Calculate portfolio metrics
        total_value = holdings_df['current_value'].sum()
        num_holdings = len(holdings_df)

        # Create snapshot record
        snapshot = {
            'timestamp': timestamp,
            'date': timestamp.date(),
            'total_value': total_value,
            'num_holdings': num_holdings,
            'source': source
        }

        # Save snapshot
        self._save_snapshot(snapshot)

        # Save individual holdings
        self._save_holdings(holdings_df, timestamp)

        # Save market context if provided
        if market_context:
            self._save_market_context(market_context, timestamp)

        logger.info(f"Portfolio snapshot saved: ${total_value:,.2f} ({num_holdings} holdings)")

        return snapshot

    def _save_snapshot(self, snapshot: Dict):
        """Save portfolio snapshot to CSV."""
        snapshot_df = pd.DataFrame([snapshot])

        if self.snapshots_file.exists():
            existing = pd.read_csv(self.snapshots_file)
            # Avoid duplicates (same day)
            existing['date'] = pd.to_datetime(existing['date']).dt.date
            if snapshot['date'] not in existing['date'].values:
                combined = pd.concat([existing, snapshot_df], ignore_index=True)
                combined.to_csv(self.snapshots_file, index=False)
        else:
            snapshot_df.to_csv(self.snapshots_file, index=False)

    def _save_holdings(self, holdings_df: pd.DataFrame, timestamp: datetime):
        """Save individual holdings to history."""
        holdings_snapshot = holdings_df.copy()
        holdings_snapshot['timestamp'] = timestamp
        holdings_snapshot['date'] = timestamp.date()

        if self.holdings_file.exists():
            existing = pd.read_csv(self.holdings_file)
            combined = pd.concat([existing, holdings_snapshot], ignore_index=True)
            combined.to_csv(self.holdings_file, index=False)
        else:
            holdings_snapshot.to_csv(self.holdings_file, index=False)

    def _save_market_context(self, market_context: Dict, timestamp: datetime):
        """Save market context data to history."""
        regime = market_context.get('regime', {})

        context_record = {
            'timestamp': timestamp,
            'date': timestamp.date(),
            'regime': regime.get('regime', 'Unknown'),
            'regime_confidence': regime.get('confidence', 0),
            'spy_trend': regime.get('spy_trend', 'Unknown'),
            'spy_rsi': regime.get('spy_rsi', 50),
            'spy_above_50': regime.get('spy_above_50', False),
            'spy_above_200': regime.get('spy_above_200', False),
            'breadth_pct': regime.get('breadth_pct', 50),
            'vix_level': regime.get('vix_level', None),
            'fear_level': regime.get('fear_level', 'Unknown')
        }

        context_df = pd.DataFrame([context_record])

        if self.market_context_file.exists():
            existing = pd.read_csv(self.market_context_file)
            # Avoid duplicates (same day)
            existing['date'] = pd.to_datetime(existing['date']).dt.date
            if context_record['date'] not in existing['date'].values:
                combined = pd.concat([existing, context_df], ignore_index=True)
                combined.to_csv(self.market_context_file, index=False)
        else:
            context_df.to_csv(self.market_context_file, index=False)

    def get_market_context_history(self, days: int = 30) -> pd.DataFrame:
        """
        Get historical market context data.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame of market context history
        """
        if not self.market_context_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.market_context_file)
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff]

        return df.sort_values('date')

    def get_snapshots(self, days: int = 30) -> pd.DataFrame:
        """
        Get historical portfolio snapshots.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame of snapshots
        """
        if not self.snapshots_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.snapshots_file)
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff]

        return df.sort_values('date')

    def get_latest_snapshot(self) -> Optional[Dict]:
        """Get the most recent portfolio snapshot."""
        if not self.snapshots_file.exists():
            return None

        df = pd.read_csv(self.snapshots_file)
        if len(df) == 0:
            return None

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        latest = df.sort_values('timestamp', ascending=False).iloc[0]

        return latest.to_dict()

    def get_holdings_history(
        self,
        symbol: Optional[str] = None,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get historical holdings data.

        Args:
            symbol: Specific symbol to filter (None = all)
            days: Number of days to retrieve

        Returns:
            DataFrame of holdings history
        """
        if not self.holdings_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.holdings_file)
        df['date'] = pd.to_datetime(df['date'])

        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        df = df[df['date'] >= cutoff]

        # Filter by symbol if specified
        if symbol:
            df = df[df['symbol'] == symbol]

        return df.sort_values('date')

    def calculate_returns(self, days: int = 30) -> Dict:
        """
        Calculate portfolio returns over time.

        Args:
            days: Period to calculate returns

        Returns:
            Dictionary with return metrics
        """
        snapshots = self.get_snapshots(days=days)

        if len(snapshots) < 2:
            return {
                'total_return': 0,
                'total_return_pct': 0,
                'daily_returns': [],
                'error': 'Insufficient data'
            }

        # Calculate total return
        start_value = snapshots.iloc[0]['total_value']
        end_value = snapshots.iloc[-1]['total_value']
        total_return = end_value - start_value
        total_return_pct = (total_return / start_value) * 100

        # Calculate daily returns
        snapshots['daily_return'] = snapshots['total_value'].pct_change() * 100
        daily_returns = snapshots['daily_return'].dropna().tolist()

        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'daily_returns': daily_returns,
            'start_value': start_value,
            'end_value': end_value,
            'num_days': len(snapshots)
        }

    def get_current_holdings(self) -> pd.DataFrame:
        """Get the most recent holdings."""
        if not self.holdings_file.exists():
            return pd.DataFrame()

        df = pd.read_csv(self.holdings_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Get latest timestamp
        latest_time = df['timestamp'].max()

        # Get all holdings from latest snapshot
        latest_holdings = df[df['timestamp'] == latest_time]

        return latest_holdings

    def update_prices(self, holdings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Update current prices for holdings using yfinance.

        Args:
            holdings_df: DataFrame with 'symbol' column

        Returns:
            Updated DataFrame with current prices
        """
        symbols = holdings_df['symbol'].tolist()

        logger.info(f"Fetching current prices for {len(symbols)} stocks...")

        updated = holdings_df.copy()
        prices = {}

        try:
            # Fetch prices in batch
            tickers = yf.Tickers(' '.join(symbols))

            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')

                    if current_price:
                        prices[symbol] = current_price
                    else:
                        logger.warning(f"No price found for {symbol}")

                except Exception as e:
                    logger.warning(f"Error fetching price for {symbol}: {e}")

            # Update prices
            if 'current_price' not in updated.columns:
                updated['current_price'] = 0.0

            for symbol, price in prices.items():
                updated.loc[updated['symbol'] == symbol, 'current_price'] = price

            # Recalculate values if shares column exists
            if 'shares' in updated.columns:
                updated['current_value'] = updated['shares'] * updated['current_price']

            logger.success(f"Updated prices for {len(prices)}/{len(symbols)} stocks")

        except Exception as e:
            logger.error(f"Error updating prices: {e}")

        return updated

    def calculate_daily_change(self) -> Optional[Dict]:
        """
        Calculate change since yesterday.

        Returns:
            Dictionary with daily change metrics
        """
        snapshots = self.get_snapshots(days=7)

        if len(snapshots) < 2:
            return None

        # Get today and yesterday
        today = snapshots.iloc[-1]
        yesterday = snapshots.iloc[-2]

        change = today['total_value'] - yesterday['total_value']
        change_pct = (change / yesterday['total_value']) * 100

        return {
            'value_today': today['total_value'],
            'value_yesterday': yesterday['total_value'],
            'change': change,
            'change_pct': change_pct,
            'date_today': today['date'],
            'date_yesterday': yesterday['date']
        }

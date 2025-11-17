"""
Robinhood Export Utility

Exports portfolio recommendations in a format optimized for manual trading on Robinhood.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from loguru import logger


def export_for_robinhood(
    portfolio_df: pd.DataFrame,
    num_stocks: int = 20,
    exclude_symbols: Optional[List[str]] = None,
    total_investment: float = 10000,
    output_dir: str = "results/exports"
) -> tuple[pd.DataFrame, str]:
    """
    Export portfolio for Robinhood trading.

    Args:
        portfolio_df: Full portfolio DataFrame (sorted by weight/rank)
        num_stocks: Number of stocks to trade (default: 20)
        exclude_symbols: List of symbols to exclude (e.g., ['TSLA'])
        total_investment: Total $ to invest (default: $10,000)
        output_dir: Directory to save export file

    Returns:
        Tuple of (trading_df, filepath)
    """
    if exclude_symbols is None:
        exclude_symbols = []

    # Filter out excluded stocks
    available_stocks = portfolio_df[~portfolio_df['symbol'].isin(exclude_symbols)].copy()

    if len(available_stocks) < num_stocks:
        logger.warning(f"Only {len(available_stocks)} stocks available after exclusions")
        num_stocks = len(available_stocks)

    # Select top N stocks
    selected_stocks = available_stocks.head(num_stocks).copy()

    # Recalculate weights to sum to 100%
    original_weights = selected_stocks['weight'].values
    normalized_weights = original_weights / original_weights.sum()

    # Calculate dollar amounts
    selected_stocks['normalized_weight'] = normalized_weights
    selected_stocks['dollar_amount'] = normalized_weights * total_investment

    # Get current price if available
    if 'current_price' not in selected_stocks.columns:
        # Add placeholder
        selected_stocks['current_price'] = None
        selected_stocks['shares_to_buy'] = None
        selected_stocks['actual_cost'] = None
    else:
        # Calculate shares to buy (rounded down to avoid overspending)
        selected_stocks['shares_to_buy'] = (
            selected_stocks['dollar_amount'] / selected_stocks['current_price']
        ).apply(lambda x: int(x) if pd.notna(x) else None)

        # Calculate actual cost
        selected_stocks['actual_cost'] = (
            selected_stocks['shares_to_buy'] * selected_stocks['current_price']
        )

    # Create trading export
    trading_df = pd.DataFrame({
        'Rank': range(1, len(selected_stocks) + 1),
        'Symbol': selected_stocks['symbol'].values,
        'Weight_%': (normalized_weights * 100).round(2),
        'Target_Amount_$': selected_stocks['dollar_amount'].round(2),
        'Current_Price': selected_stocks.get('current_price', None),
        'Shares_to_Buy': selected_stocks.get('shares_to_buy', None),
        'Actual_Cost_$': selected_stocks.get('actual_cost', None),
        'Momentum_Return_%': (selected_stocks['momentum_return'] * 100).round(2),
        'LLM_Score': selected_stocks.get('llm_score', None)
    })

    # Add summary rows
    total_row = pd.DataFrame({
        'Rank': ['TOTAL'],
        'Symbol': [''],
        'Weight_%': [100.00],
        'Target_Amount_$': [total_investment],
        'Current_Price': [None],
        'Shares_to_Buy': [None],
        'Actual_Cost_$': [trading_df['Actual_Cost_$'].sum() if trading_df['Actual_Cost_$'].notna().any() else None],
        'Momentum_Return_%': [None],
        'LLM_Score': [None]
    })

    trading_df_with_total = pd.concat([trading_df, total_row], ignore_index=True)

    # Export to CSV
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = output_path / f"robinhood_orders_{num_stocks}stocks_{timestamp}.csv"

    trading_df_with_total.to_csv(filename, index=False)

    logger.info(f"Robinhood export saved to: {filename}")

    return trading_df, str(filename)


def generate_trading_instructions(
    trading_df: pd.DataFrame,
    total_investment: float,
    excluded_stocks: Optional[List[str]] = None
) -> str:
    """
    Generate step-by-step trading instructions for Robinhood.

    Args:
        trading_df: Trading DataFrame from export_for_robinhood
        total_investment: Total investment amount
        excluded_stocks: List of excluded symbols

    Returns:
        Formatted instructions string
    """
    num_stocks = len(trading_df)

    instructions = []
    instructions.append("=" * 80)
    instructions.append("ROBINHOOD TRADING INSTRUCTIONS")
    instructions.append("=" * 80)
    instructions.append("")

    # Summary
    instructions.append(f"📊 Portfolio Summary:")
    instructions.append(f"  • Number of stocks: {num_stocks}")
    instructions.append(f"  • Total investment: ${total_investment:,.2f}")
    instructions.append(f"  • Average per stock: ${total_investment/num_stocks:,.2f}")

    if excluded_stocks and len(excluded_stocks) > 0:
        instructions.append(f"  • Excluded stocks: {', '.join(excluded_stocks)}")
        instructions.append(f"  • Auto-filled with next ranked stocks")

    instructions.append("")
    instructions.append("=" * 80)
    instructions.append("STEP-BY-STEP GUIDE")
    instructions.append("=" * 80)
    instructions.append("")

    # Step 1
    instructions.append("STEP 1: Download the CSV file")
    instructions.append("  ✓ File saved to: results/exports/")
    instructions.append("  ✓ Open in Excel or Google Sheets for reference")
    instructions.append("")

    # Step 2
    instructions.append("STEP 2: Login to Robinhood")
    instructions.append("  1. Go to robinhood.com or open Robinhood app")
    instructions.append("  2. Login to your account")
    instructions.append("  3. Ensure you have sufficient buying power")
    instructions.append(f"     Required: ${total_investment:,.2f} + buffer for price changes")
    instructions.append("")

    # Step 3
    instructions.append("STEP 3: Place Orders (One by One)")
    instructions.append("  For each stock in the CSV:")
    instructions.append("")
    instructions.append("  1. Search for the ticker symbol (e.g., 'AAPL')")
    instructions.append("  2. Click 'Trade' or 'Buy'")
    instructions.append("  3. Select 'Dollars' (recommended) or 'Shares':")
    instructions.append("")
    instructions.append("     Option A - BY DOLLARS (Easier):")
    instructions.append("       • Choose 'Dollars'")
    instructions.append("       • Enter amount from 'Target_Amount_$' column")
    instructions.append(f"       • Example: For rank #1, enter ${trading_df.iloc[0]['Target_Amount_$']:.2f}")
    instructions.append("       • Robinhood calculates shares automatically (can buy fractional)")
    instructions.append("")
    instructions.append("     Option B - BY SHARES (More precise):")
    instructions.append("       • Choose 'Shares'")
    instructions.append("       • Enter number from 'Shares_to_Buy' column")
    instructions.append("       • NOTE: Some stocks may require whole shares only")
    instructions.append("")
    instructions.append("  4. Order type: 'Market Order' (executes immediately)")
    instructions.append("  5. Time in force: 'Good for day'")
    instructions.append("  6. Review and confirm order")
    instructions.append("  7. Repeat for all stocks in list")
    instructions.append("")

    # Step 4
    instructions.append("STEP 4: Verify Your Portfolio")
    instructions.append("  1. Go to 'Account' → 'Investing'")
    instructions.append(f"  2. Verify you have all {num_stocks} positions")
    instructions.append("  3. Check total invested ≈ ${total_investment:,.2f}")
    instructions.append("  4. Save your portfolio allocation for next rebalancing")
    instructions.append("")

    # Tips
    instructions.append("=" * 80)
    instructions.append("💡 TIPS FOR SUCCESS")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("1. MARKET HOURS:")
    instructions.append("   • Best to trade during market hours (9:30 AM - 4:00 PM ET)")
    instructions.append("   • Market orders execute at current price")
    instructions.append("   • Prices can change between generating portfolio and executing")
    instructions.append("")
    instructions.append("2. ORDER TYPE:")
    instructions.append("   • Market orders: Execute immediately at current price")
    instructions.append("   • Limit orders: Execute only at your specified price (slower)")
    instructions.append("   • For 20 stocks, market orders are usually fine")
    instructions.append("")
    instructions.append("3. FRACTIONAL SHARES:")
    instructions.append("   • Robinhood supports fractional shares for most stocks")
    instructions.append("   • Buying by $ amount is easier and more accurate")
    instructions.append("   • Buying by shares may require rounding (use whole numbers)")
    instructions.append("")
    instructions.append("4. REBALANCING:")
    instructions.append("   • Save this CSV file with date")
    instructions.append("   • Next month, compare new portfolio with current holdings")
    instructions.append("   • Sell stocks no longer in top 20")
    instructions.append("   • Buy new stocks that entered top 20")
    instructions.append("")

    # Warnings
    instructions.append("=" * 80)
    instructions.append("⚠️  IMPORTANT WARNINGS")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("1. This is NOT financial advice - do your own research")
    instructions.append("2. Past performance does not guarantee future results")
    instructions.append("3. You can lose money investing in stocks")
    instructions.append("4. Only invest what you can afford to lose")
    instructions.append("5. Consider consulting a financial advisor")
    instructions.append("")

    return "\n".join(instructions)


def parse_robinhood_holdings(csv_path: str) -> pd.DataFrame:
    """
    Parse Robinhood holdings CSV export.

    Args:
        csv_path: Path to Robinhood CSV file

    Returns:
        DataFrame with columns ['symbol', 'shares', 'current_value', 'avg_cost', 'current_price']
    """
    # Robinhood CSV format (as of 2025):
    # name,symbol,shares,price,averageCost,totalReturn,equity

    df = pd.read_csv(csv_path)

    # Remove empty rows
    df = df.dropna(subset=['symbol'] if 'symbol' in df.columns else df.columns[:2])

    # Normalize column names (handle both spaces and camelCase)
    df.columns = df.columns.str.strip().str.lower()

    # Map common column name variations
    column_mapping = {
        'symbol': ['symbol', 'ticker'],
        'shares': ['quantity', 'shares', 'qty'],
        'current_price': ['price', 'current price', 'last price', 'currentprice'],
        'avg_cost': ['averagecost', 'average cost', 'avg cost', 'cost basis', 'costbasis'],
        'current_value': ['equity', 'total value', 'totalvalue', 'market value', 'marketvalue']
    }

    normalized_df = {}
    for target_col, possible_names in column_mapping.items():
        found = False
        for name in possible_names:
            if name in df.columns:
                normalized_df[target_col] = df[name]
                found = True
                break

        # If not found and it's current_value, we can calculate it later
        if not found and target_col == 'current_value':
            continue
        elif not found:
            logger.warning(f"Column '{target_col}' not found in CSV. Available columns: {list(df.columns)}")

    result_df = pd.DataFrame(normalized_df)

    # Calculate current value if not present
    if 'current_value' not in result_df.columns:
        if 'shares' in result_df.columns and 'current_price' in result_df.columns:
            result_df['current_value'] = result_df['shares'] * result_df['current_price']
        else:
            raise ValueError("Cannot calculate current_value: missing 'shares' or 'current_price' columns")

    # Calculate total portfolio value
    total_value = result_df['current_value'].sum()
    result_df['current_weight'] = result_df['current_value'] / total_value

    logger.info(f"Parsed {len(result_df)} holdings from Robinhood CSV")
    logger.info(f"Total portfolio value: ${total_value:,.2f}")

    return result_df


def calculate_rebalancing_trades(
    current_holdings: pd.DataFrame,
    new_portfolio: pd.DataFrame,
    total_portfolio_value: float,
    num_stocks: int = 20,
    rebalance_threshold: float = 0.05
) -> tuple[pd.DataFrame, dict]:
    """
    Calculate what trades are needed to rebalance from current to new portfolio.

    Args:
        current_holdings: DataFrame with columns ['symbol', 'shares', 'current_value', 'current_weight']
        new_portfolio: New portfolio recommendations with 'symbol' and 'weight'
        total_portfolio_value: Total $ value of current portfolio
        num_stocks: Number of stocks in target portfolio
        rebalance_threshold: Only rebalance if weight difference > this (default 5%)

    Returns:
        Tuple of (trades_df, summary_dict)
    """
    # Get new target stocks and their weights
    target_portfolio = new_portfolio.head(num_stocks).copy()

    # Normalize weights to sum to 100%
    target_portfolio['target_weight'] = (
        target_portfolio['weight'] / target_portfolio['weight'].sum()
    )

    # Get stock sets
    target_stocks = set(target_portfolio['symbol'].values)
    current_stocks = set(current_holdings['symbol'].values)

    # Stocks to sell (in current but not in target)
    to_sell = current_stocks - target_stocks

    # Stocks to buy (in target but not in current)
    to_buy = target_stocks - current_stocks

    # Stocks to hold (in both)
    to_hold = current_stocks & target_stocks

    # Create trades list
    trades = []

    # Calculate total proceeds from sells
    total_sell_proceeds = 0

    # Add sells
    for symbol in to_sell:
        current_row = current_holdings[current_holdings['symbol'] == symbol].iloc[0]
        sell_value = current_row['current_value']
        total_sell_proceeds += sell_value

        trades.append({
            'Action': 'SELL',
            'Symbol': symbol,
            'Current_Shares': current_row['shares'],
            'Current_Value_$': sell_value,
            'Current_Weight_%': current_row['current_weight'] * 100,
            'Target_Weight_%': 0,
            'Reason': f'No longer in top {num_stocks}'
        })

    # Calculate available capital for buys (sell proceeds + any weight reduction from rebalancing)
    available_capital = total_sell_proceeds

    # Check holdings that need rebalancing
    rebalance_sells = []
    rebalance_buys = []

    for symbol in to_hold:
        current_row = current_holdings[current_holdings['symbol'] == symbol].iloc[0]
        target_row = target_portfolio[target_portfolio['symbol'] == symbol].iloc[0]

        current_weight = current_row['current_weight']
        target_weight = target_row['target_weight']
        weight_diff = target_weight - current_weight

        # Only rebalance if difference exceeds threshold
        if abs(weight_diff) > rebalance_threshold:
            current_value = current_row['current_value']
            target_value = target_weight * total_portfolio_value
            value_diff = target_value - current_value

            if value_diff < 0:  # Need to reduce position
                available_capital += abs(value_diff)
                rebalance_sells.append({
                    'Action': 'REBALANCE (Reduce)',
                    'Symbol': symbol,
                    'Current_Shares': current_row['shares'],
                    'Current_Value_$': current_value,
                    'Current_Weight_%': current_weight * 100,
                    'Target_Weight_%': target_weight * 100,
                    'Amount_to_Sell_$': abs(value_diff),
                    'Reason': f'Overweight by {abs(weight_diff)*100:.1f}%'
                })
            else:  # Need to increase position
                rebalance_buys.append({
                    'Action': 'REBALANCE (Add)',
                    'Symbol': symbol,
                    'Current_Shares': current_row['shares'],
                    'Current_Value_$': current_value,
                    'Current_Weight_%': current_weight * 100,
                    'Target_Weight_%': target_weight * 100,
                    'Amount_to_Buy_$': value_diff,
                    'Reason': f'Underweight by {weight_diff*100:.1f}%'
                })

    # Add new buys
    for symbol in to_buy:
        target_row = target_portfolio[target_portfolio['symbol'] == symbol].iloc[0]
        target_weight = target_row['target_weight']
        target_value = target_weight * total_portfolio_value

        trades.append({
            'Action': 'BUY',
            'Symbol': symbol,
            'Current_Shares': 0,
            'Current_Value_$': 0,
            'Current_Weight_%': 0,
            'Target_Weight_%': target_weight * 100,
            'Amount_to_Buy_$': target_value,
            'Reason': f'New entry to top {num_stocks}',
            'Rank': int(target_row.name) + 1  # Portfolio rank
        })

    # Combine all trades
    all_trades = trades + rebalance_sells + rebalance_buys
    trades_df = pd.DataFrame(all_trades)

    # Sort by action priority: SELL first, then REBALANCE (Reduce), then BUY/REBALANCE (Add)
    action_priority = {
        'SELL': 1,
        'REBALANCE (Reduce)': 2,
        'BUY': 3,
        'REBALANCE (Add)': 4
    }
    if len(trades_df) > 0:
        trades_df['_priority'] = trades_df['Action'].map(action_priority)
        trades_df = trades_df.sort_values('_priority').drop('_priority', axis=1)

    # Generate summary
    # Calculate turnover rate: percentage of portfolio that changed
    # Formula: (number of stocks that changed) / (total stocks in portfolio)
    # Where "changed" = max(sells, buys) to avoid double counting
    num_changed = max(len(to_sell), len(to_buy))
    turnover_rate = num_changed / num_stocks if num_stocks > 0 else 0

    summary = {
        'total_portfolio_value': total_portfolio_value,
        'num_stocks_to_sell': len(to_sell),
        'num_stocks_to_buy': len(to_buy),
        'num_stocks_to_rebalance': len([t for t in all_trades if 'REBALANCE' in t['Action']]),
        'num_stocks_to_hold': len([s for s in to_hold if s not in [t['Symbol'] for t in rebalance_sells + rebalance_buys]]),
        'total_sell_amount': sum([t.get('Current_Value_$', 0) + t.get('Amount_to_Sell_$', 0)
                                   for t in all_trades if 'SELL' in t['Action'] or 'Reduce' in t['Action']]),
        'total_buy_amount': sum([t.get('Amount_to_Buy_$', 0)
                                  for t in all_trades if 'BUY' in t['Action'] or 'Add' in t['Action']]),
        'turnover_rate': turnover_rate
    }

    return trades_df, summary


def generate_rebalancing_instructions(
    trades_df: pd.DataFrame,
    summary: dict,
    excluded_stocks: Optional[List[str]] = None
) -> str:
    """
    Generate step-by-step rebalancing instructions for Robinhood.

    Args:
        trades_df: DataFrame of trades from calculate_rebalancing_trades
        summary: Summary dict from calculate_rebalancing_trades
        excluded_stocks: List of excluded symbols

    Returns:
        Formatted rebalancing instructions
    """
    instructions = []
    instructions.append("=" * 80)
    instructions.append("MONTHLY PORTFOLIO REBALANCING INSTRUCTIONS")
    instructions.append("=" * 80)
    instructions.append("")

    # Summary
    instructions.append("📊 Rebalancing Summary:")
    instructions.append(f"  • Current portfolio value: ${summary['total_portfolio_value']:,.2f}")
    instructions.append(f"  • Stocks to SELL completely: {summary['num_stocks_to_sell']}")
    instructions.append(f"  • Stocks to BUY (new): {summary['num_stocks_to_buy']}")
    instructions.append(f"  • Stocks to REBALANCE: {summary['num_stocks_to_rebalance']}")
    instructions.append(f"  • Stocks to HOLD (no change): {summary['num_stocks_to_hold']}")
    instructions.append(f"  • Portfolio turnover: {summary['turnover_rate']*100:.1f}%")

    if excluded_stocks and len(excluded_stocks) > 0:
        instructions.append(f"  • Excluded stocks: {', '.join(excluded_stocks)}")

    instructions.append("")
    instructions.append(f"  💰 Total to sell: ${summary['total_sell_amount']:,.2f}")
    instructions.append(f"  💰 Total to buy: ${summary['total_buy_amount']:,.2f}")
    instructions.append("")

    # Order of operations
    instructions.append("=" * 80)
    instructions.append("⚠️  IMPORTANT: ORDER OF OPERATIONS")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("Execute trades in this exact order to avoid cash shortfalls:")
    instructions.append("  1. SELL positions that are being eliminated")
    instructions.append("  2. REDUCE positions that are overweight (partial sells)")
    instructions.append("  3. BUY new positions")
    instructions.append("  4. ADD to positions that are underweight (partial buys)")
    instructions.append("")
    instructions.append("This ensures you have cash from sells before making buys.")
    instructions.append("")

    # Detailed trade instructions
    if len(trades_df) > 0:
        instructions.append("=" * 80)
        instructions.append("STEP-BY-STEP TRADE INSTRUCTIONS")
        instructions.append("=" * 80)
        instructions.append("")

        # Group trades by action
        sells = trades_df[trades_df['Action'] == 'SELL']
        rebalance_reduces = trades_df[trades_df['Action'] == 'REBALANCE (Reduce)']
        buys = trades_df[trades_df['Action'] == 'BUY']
        rebalance_adds = trades_df[trades_df['Action'] == 'REBALANCE (Add)']

        # STEP 1: Complete sells
        if len(sells) > 0:
            instructions.append("STEP 1: SELL Complete Positions")
            instructions.append("-" * 80)
            for idx, row in sells.iterrows():
                instructions.append(f"  🔴 SELL ALL shares of {row['Symbol']}")
                instructions.append(f"     Current: {row['Current_Shares']:.2f} shares @ ${row['Current_Value_$']:,.2f}")
                instructions.append(f"     Reason: {row['Reason']}")
                instructions.append("")
            instructions.append("")

        # STEP 2: Partial sells (rebalance reduce)
        if len(rebalance_reduces) > 0:
            instructions.append("STEP 2: REDUCE Overweight Positions")
            instructions.append("-" * 80)
            for idx, row in rebalance_reduces.iterrows():
                instructions.append(f"  🟠 REDUCE position in {row['Symbol']}")
                instructions.append(f"     Current weight: {row['Current_Weight_%']:.1f}% → Target: {row['Target_Weight_%']:.1f}%")
                instructions.append(f"     SELL ${row['Amount_to_Sell_$']:,.2f} worth")
                instructions.append(f"     Reason: {row['Reason']}")
                instructions.append("")
            instructions.append("")

        # STEP 3: New buys
        if len(buys) > 0:
            instructions.append("STEP 3: BUY New Positions")
            instructions.append("-" * 80)
            for idx, row in buys.iterrows():
                rank_info = f" (Rank #{int(row['Rank'])})" if 'Rank' in row and pd.notna(row['Rank']) else ""
                instructions.append(f"  🟢 BUY {row['Symbol']}{rank_info}")
                instructions.append(f"     Target weight: {row['Target_Weight_%']:.1f}%")
                instructions.append(f"     BUY ${row['Amount_to_Buy_$']:,.2f} worth")
                instructions.append(f"     Reason: {row['Reason']}")
                instructions.append("")
            instructions.append("")

        # STEP 4: Partial buys (rebalance add)
        if len(rebalance_adds) > 0:
            instructions.append("STEP 4: ADD to Underweight Positions")
            instructions.append("-" * 80)
            for idx, row in rebalance_adds.iterrows():
                instructions.append(f"  🔵 ADD to position in {row['Symbol']}")
                instructions.append(f"     Current weight: {row['Current_Weight_%']:.1f}% → Target: {row['Target_Weight_%']:.1f}%")
                instructions.append(f"     BUY ${row['Amount_to_Buy_$']:,.2f} worth")
                instructions.append(f"     Reason: {row['Reason']}")
                instructions.append("")
            instructions.append("")

    # How to execute on Robinhood
    instructions.append("=" * 80)
    instructions.append("💡 HOW TO EXECUTE ON ROBINHOOD")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("For SELL orders:")
    instructions.append("  1. Search for the ticker symbol")
    instructions.append("  2. Click 'Trade' → 'Sell'")
    instructions.append("  3. Select 'Shares' and enter the number to sell (or 'All' for complete sells)")
    instructions.append("  4. Order type: 'Market Order' (executes immediately)")
    instructions.append("  5. Confirm and execute")
    instructions.append("")
    instructions.append("For BUY orders:")
    instructions.append("  1. Search for the ticker symbol")
    instructions.append("  2. Click 'Trade' → 'Buy'")
    instructions.append("  3. Select 'Dollars' and enter the dollar amount from instructions")
    instructions.append("  4. Order type: 'Market Order' (executes immediately)")
    instructions.append("  5. Confirm and execute")
    instructions.append("")

    # Tips
    instructions.append("=" * 80)
    instructions.append("💡 REBALANCING TIPS")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("1. TIMING:")
    instructions.append("   • Execute during market hours (9:30 AM - 4:00 PM ET)")
    instructions.append("   • Best to rebalance on the same day each month for consistency")
    instructions.append("   • Complete all trades in one session if possible")
    instructions.append("")
    instructions.append("2. REBALANCING THRESHOLD:")
    instructions.append("   • Only rebalance stocks where weight difference > 5%")
    instructions.append("   • This reduces trading costs and tax implications")
    instructions.append("   • Small deviations will self-correct over time")
    instructions.append("")
    instructions.append("3. TAX CONSIDERATIONS:")
    instructions.append("   • Selling winners = capital gains taxes")
    instructions.append("   • Consider holding winners >1 year for long-term cap gains rate")
    instructions.append("   • Consult a tax advisor for your specific situation")
    instructions.append("")
    instructions.append("4. TRACKING:")
    instructions.append("   • Save this month's portfolio CSV with date")
    instructions.append("   • Compare performance vs last month")
    instructions.append("   • Track turnover rate (ideally < 50% per month)")
    instructions.append("")

    # Warnings
    instructions.append("=" * 80)
    instructions.append("⚠️  IMPORTANT WARNINGS")
    instructions.append("=" * 80)
    instructions.append("")
    instructions.append("1. This is NOT financial advice - do your own research")
    instructions.append("2. High turnover = more trading costs + taxes")
    instructions.append("3. Market orders execute at current price (may differ from expected)")
    instructions.append("4. Consider setting aside cash for taxes on gains")
    instructions.append("5. Review trades before executing - momentum can reverse quickly")
    instructions.append("")

    return "\n".join(instructions)

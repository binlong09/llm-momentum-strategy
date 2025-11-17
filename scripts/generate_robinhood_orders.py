"""
Generate Robinhood-Ready Order List
Creates a simple step-by-step trade list for manual execution on Robinhood
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime
import argparse


def generate_robinhood_orders(
    portfolio_csv: str,
    capital: float,
    current_holdings_csv: str = None,
    output_file: str = None
):
    """
    Generate Robinhood order list from portfolio CSV.

    Args:
        portfolio_csv: Path to portfolio CSV from generate_portfolio.py
        capital: Total portfolio value in dollars
        current_holdings_csv: Optional CSV with current holdings
        output_file: Optional output file path
    """
    # Load new portfolio
    portfolio = pd.read_csv(portfolio_csv)

    print("="*80)
    print("ROBINHOOD ORDER LIST GENERATOR")
    print("="*80)
    print(f"Portfolio: {portfolio_csv}")
    print(f"Capital: ${capital:,.2f}")
    print(f"Target positions: {len(portfolio)}")
    print()

    # Calculate position values
    portfolio['position_value'] = portfolio['weight'] * capital
    portfolio['position_value'] = portfolio['position_value'].round(2)

    # Load current holdings if provided
    if current_holdings_csv:
        try:
            current = pd.read_csv(current_holdings_csv)
            current_symbols = set(current['symbol'].values)
        except:
            print(f"⚠️  Could not load current holdings from {current_holdings_csv}")
            current_symbols = set()
    else:
        current_symbols = set()

    new_symbols = set(portfolio['symbol'].values)

    # Categorize trades
    sells = current_symbols - new_symbols
    buys = new_symbols - current_symbols
    holds = current_symbols & new_symbols

    # Generate order list
    print("="*80)
    print("📋 STEP-BY-STEP ROBINHOOD ORDERS")
    print("="*80)
    print()

    order_list = []

    # STEP 1: SELL orders
    if sells:
        print("STEP 1: SELL ORDERS (Exit positions)")
        print("-" * 80)
        for i, symbol in enumerate(sorted(sells), 1):
            order = {
                'step': f'1.{i}',
                'action': 'SELL',
                'symbol': symbol,
                'amount': 'ALL',
                'notes': 'Sell 100% of position'
            }
            order_list.append(order)
            print(f"  1.{i}. SELL {symbol:6} → Sell 100% (all shares)")
        print()
    else:
        print("STEP 1: No sells needed")
        print()

    # STEP 2: BUY new positions
    if buys:
        print("STEP 2: BUY NEW POSITIONS")
        print("-" * 80)
        for i, symbol in enumerate(sorted(buys), 1):
            row = portfolio[portfolio['symbol'] == symbol].iloc[0]
            amount = row['position_value']
            weight = row['weight'] * 100

            order = {
                'step': f'2.{i}',
                'action': 'BUY',
                'symbol': symbol,
                'amount': f'${amount:.2f}',
                'notes': f'{weight:.2f}% of portfolio'
            }
            order_list.append(order)

            print(f"  2.{i}. BUY  {symbol:6} → ${amount:>8,.2f}  ({weight:>5.2f}%)")
        print()
    else:
        print("STEP 2: No new buys needed")
        print()

    # STEP 3: REBALANCE existing positions
    if holds:
        print("STEP 3: REBALANCE EXISTING POSITIONS")
        print("-" * 80)
        print("(Optional: Only rebalance if weight changed significantly)")
        print()

        for i, symbol in enumerate(sorted(holds), 1):
            row = portfolio[portfolio['symbol'] == symbol].iloc[0]
            amount = row['position_value']
            weight = row['weight'] * 100

            order = {
                'step': f'3.{i}',
                'action': 'ADJUST',
                'symbol': symbol,
                'amount': f'${amount:.2f}',
                'notes': f'Target: {weight:.2f}%'
            }
            order_list.append(order)

            print(f"  3.{i}. {symbol:6} → Target: ${amount:>8,.2f}  ({weight:>5.2f}%)")
            print(f"       Check current value, buy/sell to reach target")
        print()

    # Summary
    print("="*80)
    print("📊 EXECUTION SUMMARY")
    print("="*80)
    total_positions = len(sells) + len(buys) + len(holds)
    print(f"Total trades to execute: {total_positions}")
    print(f"  - Sell: {len(sells)} positions")
    print(f"  - Buy new: {len(buys)} positions")
    print(f"  - Rebalance: {len(holds)} positions (optional)")
    print()

    expected_turnover = (len(sells) + len(buys)) / max(len(current_symbols), 1) if current_symbols else 1.0
    print(f"Portfolio turnover: {expected_turnover*100:.1f}%")
    print()

    # Robinhood instructions
    print("="*80)
    print("📱 HOW TO EXECUTE ON ROBINHOOD")
    print("="*80)
    print("""
1. Open Robinhood app/website
2. For each SELL order:
   - Search for stock symbol
   - Click "Trade" → "Sell"
   - Select "Dollars" (not shares)
   - Enter amount or click "Max" to sell all
   - Choose "Market Order"
   - Review and submit

3. For each BUY order:
   - Search for stock symbol
   - Click "Trade" → "Buy"
   - Select "Dollars" (not shares)
   - Enter exact dollar amount from list
   - Choose "Market Order" or "Limit Order"
   - Review and submit

4. For REBALANCE orders (optional):
   - Check current position value
   - Calculate difference from target
   - Buy or sell the difference

⏰ Best time: 10:00 AM - 3:00 PM ET (avoid first/last 30 min)
💡 Tip: Use market orders for liquid stocks (S&P 500)
💰 Cost: $0 (Robinhood is commission-free)
""")

    # Save to CSV
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"results/robinhood_orders_{timestamp}.csv"

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    orders_df = pd.DataFrame(order_list)
    orders_df.to_csv(output_file, index=False)

    print("="*80)
    print(f"✅ Order list saved to: {output_file}")
    print("="*80)
    print()
    print("💡 You can print this file and check off orders as you execute them!")
    print()

    return orders_df


def main():
    parser = argparse.ArgumentParser(
        description="Generate Robinhood order list from portfolio"
    )
    parser.add_argument(
        'portfolio',
        type=str,
        help='Path to portfolio CSV file'
    )
    parser.add_argument(
        '--capital',
        type=float,
        required=True,
        help='Total portfolio value in dollars'
    )
    parser.add_argument(
        '--current-holdings',
        type=str,
        default=None,
        help='Path to CSV with current holdings (for trade comparison)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: results/robinhood_orders_TIMESTAMP.csv)'
    )

    args = parser.parse_args()

    generate_robinhood_orders(
        portfolio_csv=args.portfolio,
        capital=args.capital,
        current_holdings_csv=args.current_holdings,
        output_file=args.output
    )


if __name__ == "__main__":
    main()

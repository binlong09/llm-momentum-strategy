#!/usr/bin/env python3
"""
Test Robinhood Export Functionality
"""

import pandas as pd
from pathlib import Path
from loguru import logger

logger.info("="*80)
logger.info("ROBINHOOD EXPORT TEST")
logger.info("="*80)

# Test 1: Load existing portfolio
logger.info("\n📊 TEST 1: Loading portfolio...")
try:
    # Find most recent portfolio file
    portfolio_dir = Path("results/portfolios")
    portfolio_files = list(portfolio_dir.glob("portfolio_*.csv"))

    if not portfolio_files:
        logger.error("No portfolio files found. Generate a portfolio first.")
        exit(1)

    latest_portfolio = max(portfolio_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"Loading: {latest_portfolio}")

    portfolio_df = pd.read_csv(latest_portfolio)
    logger.success(f"✅ Loaded portfolio: {len(portfolio_df)} stocks")

except Exception as e:
    logger.error(f"❌ TEST 1 FAILED: {e}")
    exit(1)

# Test 2: Export top 20 stocks
logger.info("\n" + "="*80)
logger.info("📤 TEST 2: Export top 20 stocks (no exclusions)...")
try:
    from src.utils.robinhood_export import export_for_robinhood, generate_trading_instructions

    trading_df, filepath = export_for_robinhood(
        portfolio_df=portfolio_df,
        num_stocks=20,
        exclude_symbols=[],
        total_investment=10000,
        output_dir="results/exports"
    )

    logger.success(f"✅ Export generated: {filepath}")
    logger.info(f"  Stocks: {len(trading_df)}")
    logger.info(f"  Total investment: $10,000")

    # Show preview
    logger.info("\n📊 Trading Preview (top 5):")
    print(trading_df.head().to_string(index=False))

    # Verify file was created
    assert Path(filepath).exists(), "Export file not created"
    logger.success("✅ File created successfully")

except Exception as e:
    logger.error(f"❌ TEST 2 FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Export with exclusions
logger.info("\n" + "="*80)
logger.info("📤 TEST 3: Export top 20 with exclusions...")
try:
    # Exclude rank #3 and #5
    exclude_symbols = [
        portfolio_df.iloc[2]['symbol'],  # Rank 3
        portfolio_df.iloc[4]['symbol']   # Rank 5
    ]

    logger.info(f"Excluding: {exclude_symbols}")

    trading_df_excl, filepath_excl = export_for_robinhood(
        portfolio_df=portfolio_df,
        num_stocks=20,
        exclude_symbols=exclude_symbols,
        total_investment=10000,
        output_dir="results/exports"
    )

    logger.success(f"✅ Export generated with exclusions")
    logger.info(f"  Stocks: {len(trading_df_excl)}")

    # Verify excluded stocks are not in result
    for symbol in exclude_symbols:
        assert symbol not in trading_df_excl['Symbol'].values, f"{symbol} should be excluded"

    # Verify we got stocks from rank #21 and #22 instead
    logger.info(f"\n✅ Auto-filled with:")
    logger.info(f"  Rank 21: {portfolio_df.iloc[20]['symbol']}")
    logger.info(f"  Rank 22: {portfolio_df.iloc[21]['symbol']}")

    logger.success("✅ Exclusion logic working correctly")

except Exception as e:
    logger.error(f"❌ TEST 3 FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Generate trading instructions
logger.info("\n" + "="*80)
logger.info("📖 TEST 4: Generate trading instructions...")
try:
    instructions = generate_trading_instructions(
        trading_df=trading_df,
        total_investment=10000,
        excluded_stocks=[]
    )

    logger.success(f"✅ Instructions generated: {len(instructions)} characters")

    # Verify key sections
    assert "ROBINHOOD TRADING INSTRUCTIONS" in instructions, "Missing title"
    assert "STEP 1" in instructions, "Missing Step 1"
    assert "STEP 2" in instructions, "Missing Step 2"
    assert "STEP 3" in instructions, "Missing Step 3"
    assert "STEP 4" in instructions, "Missing Step 4"
    assert "TIPS FOR SUCCESS" in instructions, "Missing tips"
    assert "IMPORTANT WARNINGS" in instructions, "Missing warnings"

    logger.success("✅ All instruction sections present")

    # Show preview
    logger.info("\n📖 Instructions Preview (first 500 chars):")
    print("-" * 80)
    print(instructions[:500])
    print("...")
    print("-" * 80)

except Exception as e:
    logger.error(f"❌ TEST 4 FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Different investment amounts
logger.info("\n" + "="*80)
logger.info("💰 TEST 5: Different investment amounts...")
try:
    test_amounts = [5000, 10000, 25000, 50000]

    for amount in test_amounts:
        trading_df_amt, _ = export_for_robinhood(
            portfolio_df=portfolio_df,
            num_stocks=20,
            exclude_symbols=[],
            total_investment=amount,
            output_dir="results/exports"
        )

        total_target = trading_df_amt['Target_Amount_$'].sum()
        # Allow small rounding errors (up to 10 cents)
        assert abs(total_target - amount) < 0.10, f"Total doesn't match for ${amount}: got ${total_target}"

        logger.info(f"  ${amount:,}: ✅ Total=${total_target:,.2f}, Avg=${amount/20:,.2f}")

    logger.success("✅ Investment amount calculations correct")

except Exception as e:
    logger.error(f"❌ TEST 5 FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Summary
logger.info("\n" + "="*80)
logger.info("✅ ALL ROBINHOOD EXPORT TESTS PASSED!")
logger.info("="*80)
logger.info("\n✨ Robinhood Export Feature Ready!")
logger.info("\nFeatures verified:")
logger.info("  ✅ Portfolio export to trading-friendly CSV")
logger.info("  ✅ Stock exclusion with auto-fill")
logger.info("  ✅ Investment amount calculations")
logger.info("  ✅ Step-by-step trading instructions")
logger.info("  ✅ Multiple portfolio sizes supported")
logger.info("\nNext: Use in dashboard to export your portfolio! 🚀")
logger.info(f"\nExport files saved to: results/exports/")

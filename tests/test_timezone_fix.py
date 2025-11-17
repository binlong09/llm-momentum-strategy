#!/usr/bin/env python3
"""Test timezone fix for volatility protection"""

import pandas as pd
from datetime import datetime
from src.data import DataManager
from src.strategy.volatility_protection import VolatilityProtection

dm = DataManager()

# Get SPY data (will have timezone-aware index)
spy_data = dm.get_prices(['SPY'], use_cache=True, show_progress=False)
spy_prices = spy_data['SPY']

print(f"SPY index timezone: {spy_prices.index.tz}")
print(f"SPY data shape: {spy_prices.shape}")

# Calculate returns
spy_returns = spy_prices['adjusted_close'].pct_change().dropna()
print(f"SPY returns shape: {spy_returns.shape}")
print(f"Returns index timezone: {spy_returns.index.tz}")

# Create VolatilityProtection instance
vol_protect = VolatilityProtection()

# Test with timezone-naive date (this should trigger the fix)
# Use the most recent date from the data
latest_date = spy_returns.index[-1].replace(tzinfo=None)  # Strip timezone for test
current_date = latest_date
print(f"\nTest date: {current_date}")
print(f"Test date timezone: {current_date.tz}")
print(f"Latest data date: {spy_returns.index[-1]}")

try:
    scalar = vol_protect.calculate_volatility_scalar(spy_returns, current_date)
    print(f"\n✅ SUCCESS: Calculated volatility scalar = {scalar:.3f}")
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

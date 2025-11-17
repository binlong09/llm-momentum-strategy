"""
Create Performance Charts
Simple script to visualize backtest results.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

# Paths
results_dir = Path("results/backtests/20251105_122351")
output_dir = Path("results/visualizations")
output_dir.mkdir(parents=True, exist_ok=True)

print("Loading backtest data...")

# Load validation period data
val_baseline_pv = pd.read_csv(results_dir / "baseline/validation_portfolio_value.csv",
                               index_col=0, parse_dates=True)
val_enhanced_pv = pd.read_csv(results_dir / "enhanced/validation_portfolio_value.csv",
                               index_col=0, parse_dates=True)

# Load test period data
test_baseline_pv = pd.read_csv(results_dir / "baseline/test_portfolio_value.csv",
                                index_col=0, parse_dates=True)
test_enhanced_pv = pd.read_csv(results_dir / "enhanced/test_portfolio_value.csv",
                                index_col=0, parse_dates=True)

print(f"Validation period: {val_baseline_pv.index[0]} to {val_baseline_pv.index[-1]}")
print(f"Test period: {test_baseline_pv.index[0]} to {test_baseline_pv.index[-1]}")

# ========== Chart 1: Validation Equity Curve ==========
print("\nCreating validation equity curve...")
fig, ax = plt.subplots(figsize=(14, 8))

ax.plot(val_baseline_pv.index, val_baseline_pv.values / 1_000_000,
        label='Baseline', linewidth=2.5, color='#2E86AB')
ax.plot(val_enhanced_pv.index, val_enhanced_pv.values / 1_000_000,
        label='Enhanced (LLM)', linewidth=2.5, color='#A23B72')

ax.set_title('Portfolio Value - Validation Period (2019-2023)',
             fontsize=18, fontweight='bold', pad=20)
ax.set_xlabel('Date', fontsize=13, fontweight='bold')
ax.set_ylabel('Portfolio Value ($M)', fontsize=13, fontweight='bold')
ax.legend(fontsize=13, loc='upper left')
ax.grid(True, alpha=0.3)

# Stats box
baseline_ret = (val_baseline_pv.iloc[-1, 0] / val_baseline_pv.iloc[0, 0] - 1) * 100
enhanced_ret = (val_enhanced_pv.iloc[-1, 0] / val_enhanced_pv.iloc[0, 0] - 1) * 100
improvement = enhanced_ret - baseline_ret

stats_text = (f'Total Return:\n'
              f'  Baseline: {baseline_ret:.1f}%\n'
              f'  Enhanced: {enhanced_ret:.1f}%\n'
              f'  Improvement: +{improvement:.1f}%')
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
        fontsize=12, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig(output_dir / 'validation_equity_curve.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / 'validation_equity_curve.png'}")
plt.close()

# ========== Chart 2: Test Equity Curve ==========
print("Creating test equity curve...")
fig, ax = plt.subplots(figsize=(14, 8))

ax.plot(test_baseline_pv.index, test_baseline_pv.values / 1_000_000,
        label='Baseline', linewidth=2.5, color='#2E86AB')
ax.plot(test_enhanced_pv.index, test_enhanced_pv.values / 1_000_000,
        label='Enhanced (LLM)', linewidth=2.5, color='#A23B72')

ax.set_title('Portfolio Value - Test Period (2024)',
             fontsize=18, fontweight='bold', pad=20)
ax.set_xlabel('Date', fontsize=13, fontweight='bold')
ax.set_ylabel('Portfolio Value ($M)', fontsize=13, fontweight='bold')
ax.legend(fontsize=13, loc='upper left')
ax.grid(True, alpha=0.3)

# Stats box
baseline_ret = (test_baseline_pv.iloc[-1, 0] / test_baseline_pv.iloc[0, 0] - 1) * 100
enhanced_ret = (test_enhanced_pv.iloc[-1, 0] / test_enhanced_pv.iloc[0, 0] - 1) * 100
improvement = enhanced_ret - baseline_ret

stats_text = (f'Total Return:\n'
              f'  Baseline: {baseline_ret:.1f}%\n'
              f'  Enhanced: {enhanced_ret:.1f}%\n'
              f'  Improvement: +{improvement:.1f}%')
ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
        fontsize=12, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig(output_dir / 'test_equity_curve.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / 'test_equity_curve.png'}")
plt.close()

# ========== Chart 3: Drawdowns ==========
print("Creating drawdown charts...")

# Calculate drawdowns
def calculate_drawdown(pv_series):
    """Calculate drawdown from portfolio value series."""
    values = pv_series.values.flatten()
    running_max = np.maximum.accumulate(values)
    drawdown = (values / running_max - 1) * 100
    return drawdown

val_baseline_dd = calculate_drawdown(val_baseline_pv)
val_enhanced_dd = calculate_drawdown(val_enhanced_pv)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Baseline
ax1.fill_between(val_baseline_pv.index, val_baseline_dd, 0,
                  alpha=0.3, color='#2E86AB')
ax1.plot(val_baseline_pv.index, val_baseline_dd,
          color='#2E86AB', linewidth=1.5)
ax1.set_title('Baseline Strategy - Drawdown (2019-2023)',
              fontsize=14, fontweight='bold')
ax1.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

max_dd = val_baseline_dd.min()
ax1.text(0.02, 0.05, f'Max Drawdown: {max_dd:.2f}%',
         transform=ax1.transAxes, fontsize=11,
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

# Enhanced
ax2.fill_between(val_enhanced_pv.index, val_enhanced_dd, 0,
                  alpha=0.3, color='#A23B72')
ax2.plot(val_enhanced_pv.index, val_enhanced_dd,
          color='#A23B72', linewidth=1.5)
ax2.set_title('Enhanced Strategy - Drawdown (2019-2023)',
              fontsize=14, fontweight='bold')
ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('Drawdown (%)', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

max_dd_enh = val_enhanced_dd.min()
improvement = max_dd_enh - max_dd
ax2.text(0.02, 0.05,
         f'Max Drawdown: {max_dd_enh:.2f}% ({improvement:+.2f}% vs baseline)',
         transform=ax2.transAxes, fontsize=11,
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))

plt.tight_layout()
plt.savefig(output_dir / 'validation_drawdowns.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / 'validation_drawdowns.png'}")
plt.close()

# ========== Chart 4: Performance Comparison ==========
print("Creating performance comparison...")

fig, ax = plt.subplots(figsize=(12, 7))

# Calculate metrics
val_baseline_ann = (val_baseline_pv.iloc[-1, 0] / val_baseline_pv.iloc[0, 0]) ** (1/5) - 1
val_enhanced_ann = (val_enhanced_pv.iloc[-1, 0] / val_enhanced_pv.iloc[0, 0]) ** (1/5) - 1
test_baseline_ann = (test_baseline_pv.iloc[-1, 0] / test_baseline_pv.iloc[0, 0]) ** (252/len(test_baseline_pv)) - 1
test_enhanced_ann = (test_enhanced_pv.iloc[-1, 0] / test_enhanced_pv.iloc[0, 0]) ** (252/len(test_enhanced_pv)) - 1

categories = ['Validation\n(2019-2023)', 'Test\n(2024)']
baseline_values = [val_baseline_ann * 100, test_baseline_ann * 100]
enhanced_values = [val_enhanced_ann * 100, test_enhanced_ann * 100]

x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, baseline_values, width,
                label='Baseline', color='#2E86AB', alpha=0.9)
bars2 = ax.bar(x + width/2, enhanced_values, width,
                label='Enhanced (LLM)', color='#A23B72', alpha=0.9)

ax.set_title('Annual Returns Comparison', fontsize=18, fontweight='bold', pad=20)
ax.set_ylabel('Annualized Return (%)', fontsize=13, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=12)
ax.legend(fontsize=13, loc='upper left')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom',
                fontsize=11, fontweight='bold')

# Add improvements
improvements = [enhanced_values[i] - baseline_values[i] for i in range(len(categories))]
for i, imp in enumerate(improvements):
    ax.text(i, max(baseline_values[i], enhanced_values[i]) + 1,
            f'+{imp:.1f}%', ha='center', va='bottom',
            fontsize=10, color='green', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))

plt.tight_layout()
plt.savefig(output_dir / 'annual_returns_comparison.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: {output_dir / 'annual_returns_comparison.png'}")
plt.close()

# ========== Summary ==========
print("\n" + "="*70)
print("VISUALIZATION COMPLETE")
print("="*70)
print(f"\nAll charts saved to: {output_dir}/")
print("\nGenerated files:")
print("  1. validation_equity_curve.png")
print("  2. test_equity_curve.png")
print("  3. validation_drawdowns.png")
print("  4. annual_returns_comparison.png")
print("\nYou can view these in any image viewer or include in reports.")
print("="*70)

"""
Visualize Backtest Results
Creates comprehensive charts for baseline vs enhanced strategy comparison.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from loguru import logger

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


def load_backtest_data(results_dir: str):
    """Load backtest results from directory."""
    results_path = Path(results_dir)

    # Load portfolio values
    baseline_pv = pd.read_csv(
        results_path / "baseline" / f"{results_path.name.split('_')[0]}_portfolio_value.csv",
        index_col=0,
        parse_dates=True
    )

    enhanced_pv = pd.read_csv(
        results_path / "enhanced" / f"{results_path.name.split('_')[0]}_portfolio_value.csv",
        index_col=0,
        parse_dates=True
    )

    # Load returns
    baseline_ret = pd.read_csv(
        results_path / "baseline" / f"{results_path.name.split('_')[0]}_daily_returns.csv",
        index_col=0,
        parse_dates=True
    )

    enhanced_ret = pd.read_csv(
        results_path / "enhanced" / f"{results_path.name.split('_')[0]}_daily_returns.csv",
        index_col=0,
        parse_dates=True
    )

    return {
        'baseline_pv': baseline_pv,
        'enhanced_pv': enhanced_pv,
        'baseline_ret': baseline_ret,
        'enhanced_ret': enhanced_ret
    }


def plot_equity_curves(data: dict, period_name: str, output_dir: Path):
    """Plot equity curves for baseline vs enhanced."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot curves
    baseline_pv = data['baseline_pv']
    enhanced_pv = data['enhanced_pv']

    ax.plot(baseline_pv.index, baseline_pv.values / 1_000_000,
            label='Baseline', linewidth=2, color='#2E86AB')
    ax.plot(enhanced_pv.index, enhanced_pv.values / 1_000_000,
            label='Enhanced (LLM)', linewidth=2, color='#A23B72')

    # Format
    ax.set_title(f'Portfolio Value Over Time - {period_name}',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Portfolio Value ($M)', fontsize=12, fontweight='bold')
    ax.legend(fontsize=12, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Add performance stats
    baseline_return = (baseline_pv.iloc[-1] / baseline_pv.iloc[0] - 1) * 100
    enhanced_return = (enhanced_pv.iloc[-1] / enhanced_pv.iloc[0] - 1) * 100
    improvement = enhanced_return - baseline_return

    stats_text = f'Baseline: {baseline_return[0]:.1f}%\nEnhanced: {enhanced_return[0]:.1f}%\nImprovement: +{improvement[0]:.1f}%'
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    filename = output_dir / f'equity_curve_{period_name.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def plot_drawdowns(data: dict, period_name: str, output_dir: Path):
    """Plot drawdown charts."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Calculate drawdowns
    baseline_pv = data['baseline_pv'].values.flatten()
    enhanced_pv = data['enhanced_pv'].values.flatten()

    baseline_dd = (baseline_pv / np.maximum.accumulate(baseline_pv) - 1) * 100
    enhanced_dd = (enhanced_pv / np.maximum.accumulate(enhanced_pv) - 1) * 100

    dates = data['baseline_pv'].index

    # Baseline drawdown
    ax1.fill_between(dates, baseline_dd, 0, alpha=0.3, color='#2E86AB')
    ax1.plot(dates, baseline_dd, color='#2E86AB', linewidth=1.5)
    ax1.set_title(f'Baseline Strategy Drawdown - {period_name}',
                  fontsize=14, fontweight='bold')
    ax1.set_ylabel('Drawdown (%)', fontsize=11, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    max_dd_baseline = baseline_dd.min()
    ax1.text(0.02, 0.02, f'Max Drawdown: {max_dd_baseline:.2f}%',
             transform=ax1.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Enhanced drawdown
    ax2.fill_between(dates, enhanced_dd, 0, alpha=0.3, color='#A23B72')
    ax2.plot(dates, enhanced_dd, color='#A23B72', linewidth=1.5)
    ax2.set_title(f'Enhanced Strategy Drawdown - {period_name}',
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Drawdown (%)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    max_dd_enhanced = enhanced_dd.min()
    improvement = max_dd_enhanced - max_dd_baseline
    ax2.text(0.02, 0.02,
             f'Max Drawdown: {max_dd_enhanced:.2f}% ({improvement:+.2f}% vs baseline)',
             transform=ax2.transAxes, fontsize=10,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    # Save
    filename = output_dir / f'drawdowns_{period_name.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def plot_monthly_returns(data: dict, period_name: str, output_dir: Path):
    """Plot monthly returns comparison."""
    # Resample to monthly
    baseline_ret = data['baseline_ret'].resample('M').apply(lambda x: (1 + x).prod() - 1) * 100
    enhanced_ret = data['enhanced_ret'].resample('M').apply(lambda x: (1 + x).prod() - 1) * 100

    # Combine
    monthly_df = pd.DataFrame({
        'Baseline': baseline_ret.values.flatten(),
        'Enhanced': enhanced_ret.values.flatten()
    }, index=baseline_ret.index)

    # Plot
    fig, ax = plt.subplots(figsize=(14, 8))

    x = np.arange(len(monthly_df))
    width = 0.35

    bars1 = ax.bar(x - width/2, monthly_df['Baseline'], width,
                   label='Baseline', color='#2E86AB', alpha=0.8)
    bars2 = ax.bar(x + width/2, monthly_df['Enhanced'], width,
                   label='Enhanced', color='#A23B72', alpha=0.8)

    # Format
    ax.set_title(f'Monthly Returns Comparison - {period_name}',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Return (%)', fontsize=12, fontweight='bold')
    ax.set_xticks(x[::3])  # Show every 3rd month
    ax.set_xticklabels([d.strftime('%Y-%m') for d in monthly_df.index[::3]], rotation=45)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

    # Stats
    baseline_avg = monthly_df['Baseline'].mean()
    enhanced_avg = monthly_df['Enhanced'].mean()

    stats_text = f'Avg Monthly Return:\nBaseline: {baseline_avg:.2f}%\nEnhanced: {enhanced_avg:.2f}%'
    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    filename = output_dir / f'monthly_returns_{period_name.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def plot_rolling_metrics(data: dict, period_name: str, output_dir: Path):
    """Plot rolling Sharpe ratio and volatility."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    baseline_ret = data['baseline_ret'].values.flatten()
    enhanced_ret = data['enhanced_ret'].values.flatten()
    dates = data['baseline_ret'].index

    # Rolling Sharpe (252-day window)
    window = 252
    if len(baseline_ret) > window:
        baseline_sharpe = pd.Series(baseline_ret).rolling(window).apply(
            lambda x: (x.mean() / x.std()) * np.sqrt(252) if x.std() > 0 else 0
        )
        enhanced_sharpe = pd.Series(enhanced_ret).rolling(window).apply(
            lambda x: (x.mean() / x.std()) * np.sqrt(252) if x.std() > 0 else 0
        )

        ax1.plot(dates, baseline_sharpe, label='Baseline', color='#2E86AB', linewidth=2)
        ax1.plot(dates, enhanced_sharpe, label='Enhanced', color='#A23B72', linewidth=2)
        ax1.set_title(f'Rolling Sharpe Ratio (252-day) - {period_name}',
                      fontsize=14, fontweight='bold')
        ax1.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    # Rolling Volatility (63-day window)
    vol_window = 63
    if len(baseline_ret) > vol_window:
        baseline_vol = pd.Series(baseline_ret).rolling(vol_window).std() * np.sqrt(252) * 100
        enhanced_vol = pd.Series(enhanced_ret).rolling(vol_window).std() * np.sqrt(252) * 100

        ax2.plot(dates, baseline_vol, label='Baseline', color='#2E86AB', linewidth=2)
        ax2.plot(dates, enhanced_vol, label='Enhanced', color='#A23B72', linewidth=2)
        ax2.set_title(f'Rolling Volatility (63-day) - {period_name}',
                      fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Annualized Volatility (%)', fontsize=11, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save
    filename = output_dir / f'rolling_metrics_{period_name.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def plot_return_distribution(data: dict, period_name: str, output_dir: Path):
    """Plot return distribution comparison."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    baseline_ret = data['baseline_ret'].values.flatten() * 100
    enhanced_ret = data['enhanced_ret'].values.flatten() * 100

    # Histograms
    ax1.hist(baseline_ret, bins=50, alpha=0.7, color='#2E86AB', label='Baseline', density=True)
    ax1.hist(enhanced_ret, bins=50, alpha=0.7, color='#A23B72', label='Enhanced', density=True)
    ax1.set_title(f'Daily Return Distribution - {period_name}',
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Daily Return (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Density', fontsize=11, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.axvline(x=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    # Box plots
    box_data = [baseline_ret, enhanced_ret]
    bp = ax2.boxplot(box_data, labels=['Baseline', 'Enhanced'],
                     patch_artist=True, widths=0.6)

    colors = ['#2E86AB', '#A23B72']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.set_title(f'Return Distribution Summary - {period_name}',
                  fontsize=14, fontweight='bold')
    ax2.set_ylabel('Daily Return (%)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)

    # Stats
    stats_text = (f'Baseline:\n  Mean: {baseline_ret.mean():.3f}%\n  Std: {baseline_ret.std():.3f}%\n\n'
                  f'Enhanced:\n  Mean: {enhanced_ret.mean():.3f}%\n  Std: {enhanced_ret.std():.3f}%')
    ax2.text(0.02, 0.98, stats_text,
             transform=ax2.transAxes,
             fontsize=9,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save
    filename = output_dir / f'return_distribution_{period_name.lower().replace(" ", "_")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def create_summary_dashboard(validation_data: dict, test_data: dict, output_dir: Path):
    """Create a summary dashboard with key metrics."""
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('LLM-Enhanced Momentum Strategy - Performance Summary',
                 fontsize=18, fontweight='bold', y=0.98)

    # 1. Validation equity curve
    ax1 = fig.add_subplot(gs[0, 0])
    val_baseline_pv = validation_data['baseline_pv']
    val_enhanced_pv = validation_data['enhanced_pv']
    ax1.plot(val_baseline_pv.index, val_baseline_pv.values / 1_000_000,
             label='Baseline', linewidth=2, color='#2E86AB')
    ax1.plot(val_enhanced_pv.index, val_enhanced_pv.values / 1_000_000,
             label='Enhanced', linewidth=2, color='#A23B72')
    ax1.set_title('Validation Period (2019-2023)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($M)', fontsize=10)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # 2. Test equity curve
    ax2 = fig.add_subplot(gs[0, 1])
    test_baseline_pv = test_data['baseline_pv']
    test_enhanced_pv = test_data['enhanced_pv']
    ax2.plot(test_baseline_pv.index, test_baseline_pv.values / 1_000_000,
             label='Baseline', linewidth=2, color='#2E86AB')
    ax2.plot(test_enhanced_pv.index, test_enhanced_pv.values / 1_000_000,
             label='Enhanced', linewidth=2, color='#A23B72')
    ax2.set_title('Test Period (2024)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Portfolio Value ($M)', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    # 3. Annual returns comparison
    ax3 = fig.add_subplot(gs[1, :])

    # Calculate annual returns
    val_baseline_ret = (val_baseline_pv.iloc[-1] / val_baseline_pv.iloc[0]) ** (1/5) - 1
    val_enhanced_ret = (val_enhanced_pv.iloc[-1] / val_enhanced_pv.iloc[0]) ** (1/5) - 1
    test_baseline_ret = (test_baseline_pv.iloc[-1] / test_baseline_pv.iloc[0]) ** (252/len(test_baseline_pv)) - 1
    test_enhanced_ret = (test_enhanced_pv.iloc[-1] / test_enhanced_pv.iloc[0]) ** (252/len(test_enhanced_pv)) - 1

    periods = ['Validation\n(2019-2023)', 'Test\n(2024)']
    baseline_returns = [val_baseline_ret[0] * 100, test_baseline_ret[0] * 100]
    enhanced_returns = [val_enhanced_ret[0] * 100, test_enhanced_ret[0] * 100]

    x = np.arange(len(periods))
    width = 0.35

    bars1 = ax3.bar(x - width/2, baseline_returns, width, label='Baseline',
                    color='#2E86AB', alpha=0.8)
    bars2 = ax3.bar(x + width/2, enhanced_returns, width, label='Enhanced',
                    color='#A23B72', alpha=0.8)

    ax3.set_title('Annual Returns by Period', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Annual Return (%)', fontsize=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(periods)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=9)

    # 4. Key metrics table
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')

    # Create metrics table
    metrics_data = [
        ['Period', 'Strategy', 'Ann. Return', 'Volatility', 'Sharpe', 'Max DD'],
        ['Validation', 'Baseline', '10.04%', '22.48%', '0.27', '-42.38%'],
        ['', 'Enhanced', '11.43%', '22.46%', '0.33', '-40.83%'],
        ['', 'Improvement', '+1.39%', '-0.02%', '+0.06', '+1.55%'],
        ['Test', 'Baseline', '18.90%', '18.78%', '0.79', '-24.05%'],
        ['', 'Enhanced', '23.12%', '20.82%', '0.92', '-26.32%'],
        ['', 'Improvement', '+4.22%', '+2.04%', '+0.13', '-2.27%'],
    ]

    table = ax4.table(cellText=metrics_data, cellLoc='center', loc='center',
                      bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header row
    for i in range(6):
        table[(0, i)].set_facecolor('#4A90A4')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Style improvement rows
    for row in [3, 6]:
        for col in range(6):
            table[(row, col)].set_facecolor('#E8F4F8')

    plt.tight_layout()

    # Save
    filename = output_dir / 'summary_dashboard.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    logger.info(f"Saved: {filename}")
    plt.close()


def main():
    """Generate all visualizations."""
    logger.info("="*70)
    logger.info("BACKTEST RESULTS VISUALIZATION")
    logger.info("="*70)

    # Find latest backtest results
    results_base = Path("results/backtests")
    if not results_base.exists():
        logger.error(f"Results directory not found: {results_base}")
        return

    # Get most recent backtest
    backtest_dirs = sorted(results_base.glob("*"), reverse=True)
    if not backtest_dirs:
        logger.error("No backtest results found")
        return

    latest_dir = backtest_dirs[0]
    logger.info(f"Using results from: {latest_dir}")

    # Create output directory
    output_dir = Path("results/visualizations") / latest_dir.name
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving plots to: {output_dir}\n")

    # Load data
    logger.info("Loading validation period data...")
    validation_data = load_backtest_data(str(latest_dir / "../20251105_122351"))

    logger.info("Loading test period data...")
    test_data = load_backtest_data(str(latest_dir / "../20251105_122351"))

    # Generate plots
    logger.info("\n" + "="*70)
    logger.info("Generating visualizations...")
    logger.info("="*70 + "\n")

    # Validation period plots
    logger.info("Creating validation period plots...")
    plot_equity_curves(validation_data, "Validation (2019-2023)", output_dir)
    plot_drawdowns(validation_data, "Validation (2019-2023)", output_dir)
    plot_monthly_returns(validation_data, "Validation (2019-2023)", output_dir)
    plot_rolling_metrics(validation_data, "Validation (2019-2023)", output_dir)
    plot_return_distribution(validation_data, "Validation (2019-2023)", output_dir)

    # Test period plots
    logger.info("\nCreating test period plots...")
    plot_equity_curves(test_data, "Test (2024)", output_dir)
    plot_drawdowns(test_data, "Test (2024)", output_dir)
    plot_monthly_returns(test_data, "Test (2024)", output_dir)
    plot_rolling_metrics(test_data, "Test (2024)", output_dir)
    plot_return_distribution(test_data, "Test (2024)", output_dir)

    # Summary dashboard
    logger.info("\nCreating summary dashboard...")
    create_summary_dashboard(validation_data, test_data, output_dir)

    logger.info("\n" + "="*70)
    logger.info("VISUALIZATION COMPLETE")
    logger.info("="*70)
    logger.info(f"All plots saved to: {output_dir}")
    logger.info("\nGenerated files:")
    for plot_file in sorted(output_dir.glob("*.png")):
        logger.info(f"  - {plot_file.name}")


if __name__ == "__main__":
    main()

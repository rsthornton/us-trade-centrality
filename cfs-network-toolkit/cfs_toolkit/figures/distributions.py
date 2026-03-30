"""
Edge weight distribution visualizations.
"""

import logging
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

log = logging.getLogger(__name__)


def generate_distribution_figure(weights_51, weights_52, stats_51, stats_52, output_path):
    """
    Generate publication-quality histogram with percentile markers.

    Args:
        weights_51 (np.array): 51×51 domestic edge weights
        weights_52 (np.array): 52×52 international edge weights
        stats_51 (dict): Statistics for 51×51
        stats_52 (dict): Statistics for 52×52
        output_path (Path): Output file path
    """
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)

    # Color scheme
    color_51 = '#2E86AB'  # Blue for domestic
    color_52 = '#A23B72'  # Purple for international

    # Plot 51×51 distribution
    ax1 = axes[0]
    ax1.hist(weights_51, bins=100, color=color_51, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('Frequency', fontsize=14)
    ax1.set_title('51×51 Domestic Network - Edge Weight Distribution', fontsize=16, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # Add percentile markers for 51×51
    percentile_markers = [25, 50, 75, 90]
    for pct in percentile_markers:
        val = stats_51[f'p{pct}']
        ax1.axvline(val, color='red', linestyle='--', alpha=0.6, linewidth=1.5)
        ax1.text(val, ax1.get_ylim()[1] * 0.95, f'{pct}th',
                rotation=0, fontsize=12, ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Add summary stats text for 51×51
    stats_text_51 = (f"Edges: {stats_51['edge_count']:,}\n"
                     f"Mean: ${stats_51['mean']:,.0f}\n"
                     f"Median: ${stats_51['median']:,.0f}")
    ax1.text(0.98, 0.65, stats_text_51, transform=ax1.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Format x-axis with currency
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))

    # Plot 52×52 distribution
    ax2 = axes[1]
    ax2.hist(weights_52, bins=100, color=color_52, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax2.set_xlabel('Edge Weight (Trade Value)', fontsize=14)
    ax2.set_ylabel('Frequency', fontsize=14)
    ax2.set_title('52×52 International Network - Edge Weight Distribution', fontsize=16, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Add percentile markers for 52×52
    for pct in percentile_markers:
        val = stats_52[f'p{pct}']
        ax2.axvline(val, color='red', linestyle='--', alpha=0.6, linewidth=1.5)
        ax2.text(val, ax2.get_ylim()[1] * 0.95, f'{pct}th',
                rotation=0, fontsize=12, ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    # Add summary stats text for 52×52
    stats_text_52 = (f"Edges: {stats_52['edge_count']:,}\n"
                     f"Mean: ${stats_52['mean']:,.0f}\n"
                     f"Median: ${stats_52['median']:,.0f}")
    ax2.text(0.98, 0.65, stats_text_52, transform=ax2.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Format x-axis with currency
    ax2.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x/1e6:.0f}M'))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    log.info(f"Figure saved to {output_path}")
    plt.close()

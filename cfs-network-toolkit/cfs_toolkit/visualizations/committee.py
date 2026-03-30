"""
Committee-Friendly Comparison Visualizations
===========================================
Simple, clean visualizations that make the 51×51 vs 52×52 comparison
ultra-clear for thesis committee presentations.

Focus: Minimal design, maximum clarity, powerful storytelling.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, List, Tuple
import json


def set_committee_style():
    """Set clean, professional matplotlib style for committee presentations."""
    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 14,
        'font.family': 'Arial',
        'axes.labelsize': 15,
        'axes.titlesize': 17,
        'xtick.labelsize': 13,
        'ytick.labelsize': 13,
        'legend.fontsize': 13,
        'figure.titlesize': 19,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'figure.facecolor': 'white',
        'axes.facecolor': 'white'
    })


def create_correlation_paradox_chart(
    comparative_stats: Dict,
    measures: List[str],
    output_dir: Path
) -> None:
    """
    Create side-by-side chart showing correlation strength vs actual changes.

    Left: High correlation values (suggests stability)
    Right: Number of states that actually changed (shows reorganization)

    This directly illustrates the thesis argument.
    """
    set_committee_style()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Extract data
    correlations = comparative_stats['correlations']
    effect_sizes = comparative_stats['effect_sizes']

    # Left panel: Correlation strength
    measures_clean = [m.replace('_', ' ').title() for m in measures]
    spearman_values = [correlations[m]['spearman'] for m in measures]

    bars1 = ax1.bar(measures_clean, spearman_values,
                   color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
    ax1.set_ylim(0, 1.1)
    ax1.set_ylabel('Spearman Correlation (ρ)', fontweight='bold')
    ax1.set_title('High Correlations Suggest Stability', fontweight='bold', fontsize=13)

    # Reference line at 0.9 (very strong correlation threshold)
    ax1.axhline(y=0.9, color='red', linestyle='--', alpha=0.7, linewidth=2)

    # Add correlation values above bars
    for bar, val in zip(bars1, spearman_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{val:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Right panel: States that changed
    states_changed = [effect_sizes[m]['states_changed'] for m in measures]
    total_states = effect_sizes[measures[0]]['total_states']

    bars2 = ax2.bar(measures_clean, states_changed,
                   color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
    ax2.set_ylim(0, total_states + 10)
    ax2.set_ylabel('States with Ranking Changes', fontweight='bold')
    ax2.set_title('But Many States Actually Reorganized', fontweight='bold', fontsize=13)

    # Reference line at ~80% of states
    reference_line = total_states * 0.8
    ax2.axhline(y=reference_line, color='orange', linestyle='--', alpha=0.7, linewidth=2)

    # Add values above bars
    for bar, val in zip(bars2, states_changed):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{val}/{total_states}', ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Main title spanning both panels
    fig.suptitle('The Correlation vs. Change Paradox',
                 fontsize=18, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.subplots_adjust(top=0.90, wspace=0.3)

    # Save both formats
    plt.savefig(output_dir / 'correlation_paradox_chart.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'correlation_paradox_chart.pdf', bbox_inches='tight')
    plt.close()


def create_ranking_change_chart(
    rank_changes_df: pd.DataFrame,
    measure: str,
    output_dir: Path,
    top_n: int = 15
) -> None:
    """
    Create horizontal bar chart showing biggest ranking changes.

    Green bars: States that gained ranks (better position)
    Red bars: States that lost ranks (worse position)
    """
    set_committee_style()

    # Filter for the specific measure and get top changes
    measure_data = rank_changes_df[rank_changes_df['measure'] == measure].copy()
    measure_data = measure_data.reindex(measure_data['abs_delta_rank'].abs().sort_values(ascending=False).index)
    top_changes = measure_data.head(top_n)

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 8))

    # Color based on direction of change
    colors = ['#27AE60' if x < 0 else '#E74C3C' for x in top_changes['delta_rank']]

    bars = ax.barh(range(len(top_changes)), top_changes['delta_rank'],
                   color=colors, alpha=0.8, edgecolor='white', linewidth=1)

    # Customize axes
    ax.set_yticks(range(len(top_changes)))
    ax.set_yticklabels(top_changes['label'], fontsize=11)
    ax.set_xlabel('Ranking Change (52×52 rank - 51×51 rank)', fontweight='bold', fontsize=12)
    ax.set_title(f'{measure.replace("_", " ").title()} Centrality: Biggest Ranking Changes\n'
                f'International Integration Winners vs. Losers',
                fontweight='bold', fontsize=16, pad=20)

    # Add zero line
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.8, linewidth=1)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, top_changes['delta_rank'])):
        width = bar.get_width()
        label_x = width + (0.3 if width > 0 else -0.3)
        ax.text(label_x, bar.get_y() + bar.get_height()/2,
                f'{val:+d}', ha='left' if width > 0 else 'right',
                va='center', fontweight='bold', fontsize=10)

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#27AE60', alpha=0.8, label='Gained Ranks (Better Position)'),
        Patch(facecolor='#E74C3C', alpha=0.8, label='Lost Ranks (Worse Position)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True,
              fancybox=True, shadow=True)

    # Add explanatory text
    ax.text(0.02, 0.98, 'Negative values = improved ranking\nPositive values = worse ranking',
            transform=ax.transAxes, va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgray', alpha=0.7),
            fontsize=10)

    plt.tight_layout()

    # Save both formats
    plt.savefig(output_dir / f'ranking_changes_{measure}.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / f'ranking_changes_{measure}.pdf', bbox_inches='tight')
    plt.close()


def create_before_after_scatter(
    df_51: pd.DataFrame,
    df_52: pd.DataFrame,
    measure: str,
    output_dir: Path
) -> None:
    """
    Create scatter plot of 51×51 vs 52×52 centrality values.

    Perfect correlation = points on diagonal line
    Deviations = systematic changes despite high correlation
    """
    set_committee_style()

    # Merge data
    merged = df_51[['label', measure]].merge(
        df_52[['label', measure]], on='label', suffixes=('_51', '_52')
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    # Main scatter plot
    scatter = ax.scatter(merged[f'{measure}_51'], merged[f'{measure}_52'],
                        alpha=0.7, s=80, color='#3498DB', edgecolors='white', linewidth=1)

    # Perfect correlation line (45-degree)
    min_val = min(merged[f'{measure}_51'].min(), merged[f'{measure}_52'].min())
    max_val = max(merged[f'{measure}_51'].max(), merged[f'{measure}_52'].max())
    ax.plot([min_val, max_val], [min_val, max_val],
            'r--', alpha=0.8, linewidth=2, label='Perfect Correlation Line')

    # Highlight notable outliers
    outliers = []

    # Find states with biggest absolute changes
    merged['abs_diff'] = abs(merged[f'{measure}_52'] - merged[f'{measure}_51'])
    top_outliers = merged.nlargest(5, 'abs_diff')

    for _, row in top_outliers.iterrows():
        x, y = row[f'{measure}_51'], row[f'{measure}_52']
        ax.annotate(row['label'], (x, y),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   fontsize=10, fontweight='bold',
                   arrowprops=dict(arrowstyle='->', color='black', alpha=0.7))

    # Calculate and display correlation
    from scipy.stats import spearmanr
    corr, p_val = spearmanr(merged[f'{measure}_51'], merged[f'{measure}_52'])

    ax.text(0.05, 0.95, f'Spearman ρ = {corr:.3f}\n(p < 0.001)',
            transform=ax.transAxes, va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8),
            fontsize=12, fontweight='bold')

    # Labels and title
    measure_clean = measure.replace('_', ' ').title()
    ax.set_xlabel(f'{measure_clean} (51×51 Domestic Network)', fontweight='bold', fontsize=12)
    ax.set_ylabel(f'{measure_clean} (52×52 International Network)', fontweight='bold', fontsize=12)
    ax.set_title(f'{measure_clean} Centrality: Before vs. After International Integration\n'
                f'High Correlation with Systematic Deviations',
                fontweight='bold', fontsize=14, pad=20)

    # Legend
    ax.legend(loc='lower right', frameon=True, fancybox=True, shadow=True)

    # Equal aspect ratio for clearer comparison
    ax.set_aspect('equal', adjustable='box')

    plt.tight_layout()

    # Save both formats
    plt.savefig(output_dir / f'before_after_scatter_{measure}.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / f'before_after_scatter_{measure}.pdf', bbox_inches='tight')
    plt.close()


def create_rank_scatter(
    df_51: pd.DataFrame,
    df_52: pd.DataFrame,
    measure: str,
    output_dir: Path
) -> None:
    """
    Create scatter plot of 51×51 vs 52×52 RANKS (not values).

    Shows how state rankings changed relative to each other when international
    trade was added. Points on diagonal = no rank change.
    Points below diagonal = rank worsened (higher rank number).
    Points above diagonal = rank improved (lower rank number).

    This directly addresses: "Did states' relative positions change?"
    """
    set_committee_style()

    # Calculate ranks for each network (rank 1 = highest centrality)
    df_51_ranked = df_51.copy()
    df_52_ranked = df_52.copy()

    df_51_ranked['rank'] = df_51_ranked[measure].rank(ascending=False, method='first').astype(int)
    df_52_ranked['rank'] = df_52_ranked[measure].rank(ascending=False, method='first').astype(int)

    # Merge on state labels
    merged = df_51_ranked[['label', 'rank']].merge(
        df_52_ranked[['label', 'rank']],
        on='label',
        suffixes=('_51', '_52')
    )

    merged['rank_change'] = merged['rank_52'] - merged['rank_51']

    fig, ax = plt.subplots(figsize=(10, 10))

    # Color points by direction of change
    colors = []
    for change in merged['rank_change']:
        if change == 0:
            colors.append('#95A5A6')  # Gray for no change
        elif change < 0:
            colors.append('#27AE60')  # Green for improvement (lower rank number)
        else:
            colors.append('#E74C3C')  # Red for decline (higher rank number)

    # Main scatter plot
    scatter = ax.scatter(merged['rank_51'], merged['rank_52'],
                        alpha=0.7, s=120, c=colors, edgecolors='white', linewidth=1.5)

    # Perfect stability line (45-degree diagonal)
    max_rank = max(merged['rank_51'].max(), merged['rank_52'].max())
    ax.plot([1, max_rank], [1, max_rank],
            'k--', alpha=0.5, linewidth=2, label='No Rank Change', zorder=1)

    # Label ALL states — big changers bold, rest small (same pattern as GDP scatter)
    from adjustText import adjust_text
    merged['abs_rank_change'] = merged['rank_change'].abs()

    texts = []
    for _, row in merged.iterrows():
        x, y = row['rank_51'], row['rank_52']
        is_big_changer = row['abs_rank_change'] >= 5
        fontweight = 'bold' if is_big_changer else 'normal'
        fontsize = 11 if is_big_changer else 9
        t = ax.text(x, y, row['label'],
                    fontsize=fontsize, fontweight=fontweight,
                    ha='center', va='center')
        texts.append(t)

    adjust_text(texts, ax=ax,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.4, lw=0.5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5))

    # Count states by change direction
    n_improved = (merged['rank_change'] < 0).sum()
    n_declined = (merged['rank_change'] > 0).sum()
    n_stable = (merged['rank_change'] == 0).sum()
    total_states = len(merged)

    # Spearman correlation
    from scipy.stats import spearmanr
    rho, _ = spearmanr(merged['rank_51'], merged['rank_52'])

    # Add statistics box
    stats_text = (f"ρ = {rho:.3f}\n"
                  f"Changed: {n_improved + n_declined}/{total_states} "
                  f"({100*(n_improved + n_declined)/total_states:.0f}%)")

    ax.text(0.97, 0.03, stats_text,
            transform=ax.transAxes, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                     alpha=0.9, edgecolor='gray', linewidth=1.5),
            fontsize=14, fontweight='bold', family='monospace')

    # Labels and title
    measure_clean = measure.replace('_', ' ').title()
    ax.set_xlabel(f'Rank in 51×51 Domestic Network\n(1 = Highest {measure_clean})',
                 fontweight='bold', fontsize=16)
    ax.set_ylabel(f'Rank in 52×52 International Network\n(1 = Highest {measure_clean})',
                 fontweight='bold', fontsize=16)
    ax.set_title(f'{measure_clean} Rank Stability',
                fontweight='bold', fontsize=18, pad=15)

    # Legend for colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#27AE60', alpha=0.7, label='Rank Improved'),
        Patch(facecolor='#E74C3C', alpha=0.7, label='Rank Declined'),
        Patch(facecolor='#95A5A6', alpha=0.7, label='Unchanged'),
        plt.Line2D([0], [0], color='k', linestyle='--', linewidth=2, label='Perfect Stability')
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True,
             fancybox=True, shadow=True, fontsize=14)

    # Invert axes (rank 1 at top-left, matching GDP scatter pattern)
    ax.invert_xaxis()
    ax.invert_yaxis()

    # Grid for easier reading
    ax.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)

    plt.tight_layout()

    # Save both formats
    plt.savefig(output_dir / f'rank_scatter_{measure}.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / f'rank_scatter_{measure}.pdf', bbox_inches='tight')
    plt.close()


def generate_committee_visualizations(
    comparative_results: Dict,
    df_51: pd.DataFrame,
    df_52: pd.DataFrame,
    measures: List[str],
    output_dir: Path
) -> List[str]:
    """
    Generate all committee-friendly visualizations.

    Returns list of generated file paths.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    generated_files = []

    print("   Generating committee-friendly visualizations...")

    # 1. Correlation paradox chart
    print("      Creating correlation paradox chart...")
    create_correlation_paradox_chart(comparative_results, measures, output_dir)
    generated_files.extend([
        'correlation_paradox_chart.png',
        'correlation_paradox_chart.pdf'
    ])

    # 2. Ranking change charts for each measure
    rank_changes_df = comparative_results['rank_changes']
    for measure in measures:
        print(f"      Creating ranking change chart for {measure}...")
        create_ranking_change_chart(rank_changes_df, measure, output_dir)
        generated_files.extend([
            f'ranking_changes_{measure}.png',
            f'ranking_changes_{measure}.pdf'
        ])

    # 3. Before/after scatter plots for each measure
    for measure in measures:
        print(f"      Creating before/after scatter for {measure}...")
        create_before_after_scatter(df_51, df_52, measure, output_dir)
        generated_files.extend([
            f'before_after_scatter_{measure}.png',
            f'before_after_scatter_{measure}.pdf'
        ])

    # 4. Rank-based scatter plots for each measure (NEW)
    for measure in measures:
        print(f"      Creating rank scatter for {measure}...")
        create_rank_scatter(df_51, df_52, measure, output_dir)
        generated_files.extend([
            f'rank_scatter_{measure}.png',
            f'rank_scatter_{measure}.pdf'
        ])

    print(f"   ✓ Generated {len(generated_files)} committee visualization files")

    return generated_files
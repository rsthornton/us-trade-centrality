"""
GDP vs Network Centrality Comparison Analysis

This module compares state GDP rankings with network centrality rankings to identify
states whose structural importance exceeds or falls short of their economic size.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


def load_gdp_data(gdp_csv_path):
    """
    Load GDP data from cleaned CSV file.

    Parameters
    ----------
    gdp_csv_path : str or Path
        Path to state_gdp_2017.csv

    Returns
    -------
    dict
        Dictionary mapping state_abbrev to gdp_2017_q4_millions

    Example
    -------
    >>> gdp_dict = load_gdp_data("data/state_gdp_2017.csv")
    >>> gdp_dict['CA']
    2802289
    """
    df = pd.read_csv(gdp_csv_path)
    return dict(zip(df['state_abbrev'], df['gdp_2017_q4_millions']))


def compute_gdp_vs_centrality_comparison(centralities_df, gdp_dict):
    """
    Merge centrality rankings with GDP rankings and compute differences.

    Parameters
    ----------
    centralities_df : pd.DataFrame
        Centrality data with columns: state_id, label, eigenvector, rank_eigenvector
    gdp_dict : dict
        State abbreviation to GDP value mapping

    Returns
    -------
    pd.DataFrame
        Enriched dataframe with columns:
        - state_abbrev: 2-letter state code
        - eigenvector_rank: Network centrality rank (1 = most central)
        - gdp_value: GDP in millions
        - gdp_rank: Economic size rank (1 = largest economy)
        - rank_diff: gdp_rank - eigenvector_rank
          - Positive = structural overperformer (more central than GDP predicts)
          - Negative = structural underperformer (less central than GDP predicts)
        - eigenvector_score: Raw eigenvector centrality value
        - normalized_centrality: Eigenvector score per billion dollars of GDP
        - normalized_rank: Rank by GDP-normalized centrality (1 = highest per-GDP centrality)

    Notes
    -----
    Rank differences indicate structural position relative to economic size:
    - KY: +14 (logistics bridge connecting manufacturing regions)
    - MA: -11 (knowledge economy, structurally peripheral)
    - DC: -15 (administrative center, minimal commodity flows)

    Normalized centrality shows network importance per economic dollar:
    - High normalized centrality: Small economies with strategic network positions
    - Low normalized centrality: Large economies with limited network integration
    """
    # Add GDP values to centralities dataframe
    df = centralities_df.copy()
    df['state_abbrev'] = df['label']
    df['gdp_value'] = df['state_abbrev'].map(gdp_dict)

    # Compute GDP rank (1 = highest GDP)
    df['gdp_rank'] = df['gdp_value'].rank(ascending=False, method='min').astype(int)

    # Compute rank difference (positive = overperformer)
    df['rank_diff'] = df['gdp_rank'] - df['rank_eigenvector']

    # Compute GDP-normalized centrality (per billion dollars)
    df['normalized_centrality'] = df['eigenvector'] / (df['gdp_value'] / 1000)

    # Rank by normalized centrality (1 = highest per-GDP centrality)
    df['normalized_rank'] = df['normalized_centrality'].rank(ascending=False, method='min').astype(int)

    # Select and rename columns for clarity
    result = df[[
        'state_abbrev',
        'rank_eigenvector',
        'gdp_value',
        'gdp_rank',
        'rank_diff',
        'eigenvector',
        'normalized_centrality',
        'normalized_rank'
    ]].copy()

    result.columns = [
        'state_abbrev',
        'eigenvector_rank',
        'gdp_value',
        'gdp_rank',
        'rank_diff',
        'eigenvector_score',
        'normalized_centrality',
        'normalized_rank'
    ]

    return result.sort_values('rank_diff', ascending=False)


def identify_outliers(comparison_df, threshold=5):
    """
    Identify states with |rank_diff| >= threshold.

    Parameters
    ----------
    comparison_df : pd.DataFrame
        Output from compute_gdp_vs_centrality_comparison()
    threshold : int, default=5
        Minimum absolute rank difference to be considered an outlier

    Returns
    -------
    tuple of (list, list)
        (overperformers, underperformers)
        Each list contains tuples: (state, rank_diff, gdp_rank, eig_rank, narrative)

    Example
    -------
    >>> over, under = identify_outliers(comparison_df, threshold=5)
    >>> over[0]
    ('KY', 14, 28, 14, 'Logistics bridge connecting Midwest-Southeast manufacturing')
    """
    outliers = comparison_df[comparison_df['rank_diff'].abs() >= threshold].copy()

    overperformers = []
    underperformers = []

    for _, row in outliers.iterrows():
        state = row['state_abbrev']
        rank_diff = int(row['rank_diff'])
        gdp_rank = int(row['gdp_rank'])
        eig_rank = int(row['eigenvector_rank'])

        # Generate narrative based on state characteristics
        if rank_diff > 0:
            # Structural overperformer
            if state == 'KY':
                narrative = 'Logistics bridge connecting Midwest-Southeast manufacturing'
            elif state == 'MS':
                narrative = 'Mississippi River corridor, southeastern distribution hub'
            elif state in ['MI', 'IN', 'TN', 'OH']:
                narrative = 'Manufacturing hub with legacy supply chain connections'
            elif state in ['SC', 'LA', 'ND', 'WV', 'OK', 'MO', 'WI']:
                narrative = 'Regional connector with strategic geographic position'
            else:
                narrative = 'Structurally central despite moderate economic size'

            overperformers.append((state, rank_diff, gdp_rank, eig_rank, narrative))
        else:
            # Structural underperformer
            if state == 'MA':
                narrative = 'Knowledge economy: biotech, education, finance (limited commodity flows)'
            elif state == 'DC':
                narrative = 'Administrative center: services and government (minimal interstate trade)'
            elif state in ['CO', 'MN', 'WA']:
                narrative = 'Geographically peripheral despite large economy'
            elif state in ['CT', 'HI', 'MD', 'OR']:
                narrative = 'Large economy but regionally isolated trade patterns'
            else:
                narrative = 'Large economy with limited network integration'

            underperformers.append((state, rank_diff, gdp_rank, eig_rank, narrative))

    return overperformers, underperformers


def generate_gdp_centrality_scatter(comparison_df, output_path, label_threshold=8):
    """
    Create publication-quality scatter plot comparing GDP rank to eigenvector rank.

    Parameters
    ----------
    comparison_df : pd.DataFrame
        Output from compute_gdp_vs_centrality_comparison()
    output_path : str or Path
        Path for output PNG file (will also create PDF version)
    label_threshold : int, default=8
        Label states with |rank_diff| >= this value

    Notes
    -----
    Figure specifications:
    - Size: 8" × 6" (fits LaTeX 2-column or full-width)
    - Diagonal line: perfect correspondence (GDP rank = centrality rank)
    - Points above diagonal: structural overperformers (red)
    - Points below diagonal: structural underperformers (blue)
    - Labels for |rank_diff| >= label_threshold
    - Axes: "GDP Rank (2017 Q4)" vs "Eigenvector Centrality Rank (51×51)"
    """
    # Set publication style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 14

    fig, ax = plt.subplots(figsize=(10, 8))

    # Create color mapping (red = over, blue = under, gray = neutral)
    colors = comparison_df['rank_diff'].apply(
        lambda x: '#d62728' if x > 0 else '#1f77b4' if x < 0 else '#7f7f7f'
    )

    # Scatter plot
    ax.scatter(
        comparison_df['gdp_rank'],
        comparison_df['eigenvector_rank'],
        c=colors,
        s=80,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )

    # Diagonal reference line (perfect correspondence)
    ax.plot([0, 52], [0, 52], 'k--', alpha=0.3, linewidth=1, label='GDP = Centrality')

    # Label ALL states using adjustText for automatic overlap avoidance
    from adjustText import adjust_text
    texts = []
    for _, row in comparison_df.iterrows():
        x, y = row['gdp_rank'], row['eigenvector_rank']
        fontweight = 'bold' if abs(row['rank_diff']) >= 8 else 'normal'
        fontsize = 13 if abs(row['rank_diff']) >= 8 else 10
        t = ax.text(x, y, row['state_abbrev'],
                    fontsize=fontsize, fontweight=fontweight, ha='center', va='center')
        texts.append(t)

    adjust_text(texts, ax=ax,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.4, lw=0.5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5))

    # Axes and labels
    ax.set_xlabel('GDP Rank (2017 Q4)  ← Larger Economy', fontsize=17)
    ax.set_ylabel('Eigenvector Centrality Rank (51×51)  ← More Central', fontsize=17)
    ax.set_title(
        'Economic Size vs. Structural Position',
        fontsize=19,
        fontweight='bold',
        pad=15
    )

    # Invert axes (rank 1 = best)
    ax.invert_xaxis()
    ax.invert_yaxis()

    # Set axis limits with padding
    ax.set_xlim(54, -2)
    ax.set_ylim(54, -2)

    # Grid
    ax.grid(True, alpha=0.3)

    # Legend — upper left to avoid data in lower right
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', label='Overperformer (Centrality > GDP)'),
        Patch(facecolor='#1f77b4', label='Underperformer (Centrality < GDP)'),
        plt.Line2D([0], [0], color='k', linestyle='--', label='Perfect Correspondence')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=14,
              framealpha=0.9, edgecolor='gray')

    plt.tight_layout()

    # Save as both PNG and PDF
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()

    print(f"✓ Scatter plot saved: {output_path}")
    print(f"✓ PDF version saved: {output_path.with_suffix('.pdf')}")


def generate_normalized_centrality_bar(comparison_df, output_path, top_n=15):
    """
    Create bar chart showing GDP-normalized centrality (centrality per billion GDP).

    Parameters
    ----------
    comparison_df : pd.DataFrame
        Output from compute_gdp_vs_centrality_comparison()
    output_path : str or Path
        Path for output PNG file (will also create PDF version)
    top_n : int, default=15
        Number of top states to show

    Notes
    -----
    Shows which states have highest network centrality relative to their economic size.
    High normalized centrality = strategic network position despite small economy.
    """
    # Set publication style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 14

    # Sort by normalized centrality and take top N
    top_states = comparison_df.nlargest(top_n, 'normalized_centrality')

    fig, ax = plt.subplots(figsize=(12, 9))

    # Create color gradient based on rank difference
    colors = top_states['rank_diff'].apply(
        lambda x: '#d62728' if x > 5 else '#ff7f0e' if x > 0 else '#1f77b4' if x < -5 else '#7f7f7f'
    )

    # Horizontal bar chart
    bars = ax.barh(
        range(len(top_states)),
        top_states['normalized_centrality'],
        color=colors,
        alpha=0.7,
        edgecolor='black',
        linewidth=0.5
    )

    # State labels (larger font)
    ax.set_yticks(range(len(top_states)))
    ax.set_yticklabels(top_states['state_abbrev'], fontsize=15, fontweight='bold')

    # Add GDP and eigenvector rank annotations
    max_value = top_states['normalized_centrality'].max()
    for i, (_, row) in enumerate(top_states.iterrows()):
        value = row['normalized_centrality']
        gdp_rank = int(row['gdp_rank'])
        eig_rank = int(row['eigenvector_rank'])

        # Annotation text positioned at end of bar (not drifting)
        label = f"  GDP #{gdp_rank}, Eig #{eig_rank}"
        ax.text(value, i, label, va='center', ha='left', fontsize=14)

    # Labels and title
    ax.set_xlabel('Eigenvector Centrality per Billion Dollars GDP', fontsize=17, fontweight='bold')
    ax.set_ylabel('State', fontsize=17, fontweight='bold')
    ax.set_title(
        f'Top {top_n} States by GDP-Normalized Network Centrality\nNetwork Importance Relative to Economic Size',
        fontsize=19,
        fontweight='bold',
        pad=15
    )

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#d62728', label='Strong Overperformer (rank_diff > 5)'),
        Patch(facecolor='#ff7f0e', label='Mild Overperformer (0 < rank_diff ≤ 5)'),
        Patch(facecolor='#7f7f7f', label='Neutral (-5 ≤ rank_diff ≤ 0)'),
        Patch(facecolor='#1f77b4', label='Underperformer (rank_diff < -5)')
    ]
    ax.legend(handles=legend_elements, loc='upper center', fontsize=13,
              bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=True, fancybox=True)

    # Grid
    ax.grid(True, alpha=0.3, axis='x')

    # Set x-axis limits to give room for annotations
    ax.set_xlim(0, max_value * 1.35)

    # Invert y-axis so #1 is at top
    ax.invert_yaxis()

    plt.tight_layout()

    # Save as both PNG and PDF
    output_path = Path(output_path)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight')
    plt.close()

    print(f"✓ Normalized centrality bar chart saved: {output_path}")
    print(f"✓ PDF version saved: {output_path.with_suffix('.pdf')}")

"""
Centrality vs. Control Variable Scatter Plots

Generalized scatter function for comparing any centrality measure against
any control variable (GDP, Population, etc.) with Spearman rank correlation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import spearmanr
from adjustText import adjust_text
from matplotlib.patches import Patch


def load_population_data(pop_csv_path):
    """
    Load population data from cleaned CSV file.

    Parameters
    ----------
    pop_csv_path : str or Path
        Path to state_population_2017.csv

    Returns
    -------
    dict
        Dictionary mapping state_abbrev to pop_2017_acs
    """
    df = pd.read_csv(pop_csv_path)
    df['state_abbrev'] = df['state_abbrev'].str.strip()
    return dict(zip(df['state_abbrev'], df['pop_2017_acs']))


def generate_control_scatter(
    centralities_df, control_data, centrality_measure, control_name,
    control_unit, output_path, label_threshold=8, rank_method='first'
):
    """
    Create publication-quality scatter plot comparing a control variable rank
    to a centrality measure rank, with Spearman rho annotation.

    Parameters
    ----------
    centralities_df : pd.DataFrame
        Centrality data with columns: state_id, label, <centrality_measure>,
        rank_<centrality_measure>
    control_data : dict
        State abbreviation to control variable value mapping
    centrality_measure : str
        One of 'betweenness', 'eigenvector', 'out_degree'
    control_name : str
        Display name for the control variable (e.g., 'GDP', 'Population')
    control_unit : str
        Unit string for axis label (e.g., '2017 Q4', '2017 ACS')
    output_path : str or Path
        Path for output PNG file (will also create PDF version)
    label_threshold : int, default=8
        Label states with |rank_diff| >= this value in bold
    rank_method : str, default='first'
        Ranking method for scatter positions. 'first' gives visual separation
        for tied values (e.g., 31 states with zero betweenness).

    Returns
    -------
    tuple[float, float]
        (spearman_rho, p_value) computed with method='min' ranking
    """
    # Build working dataframe
    df = centralities_df.copy()
    df['state_abbrev'] = df['label'].str.strip()
    df['control_value'] = df['state_abbrev'].map(control_data)

    # Drop any states without control data
    df = df.dropna(subset=['control_value'])

    # Compute control rank (1 = highest value)
    df['control_rank'] = df['control_value'].rank(ascending=False, method='min').astype(int)

    # Compute centrality rank for scatter positions using specified method
    # This gives visual separation for tied values
    df['centrality_rank_scatter'] = df[centrality_measure].rank(
        ascending=False, method=rank_method
    ).astype(int)

    # Compute rank difference (positive = overperformer)
    df['rank_diff'] = df['control_rank'] - df['centrality_rank_scatter']

    # Spearman correlation using method='min' to match canonical cited values
    df['control_rank_min'] = df['control_value'].rank(ascending=False, method='min')
    df['centrality_rank_min'] = df[centrality_measure].rank(ascending=False, method='min')
    rho, p_value = spearmanr(df['control_rank_min'], df['centrality_rank_min'])

    # Clean centrality name for display
    measure_display = centrality_measure.replace('_', '-').title()
    if centrality_measure == 'out_degree':
        measure_display = 'Out-Degree'

    # Set publication style
    sns.set_style("whitegrid")
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 14

    fig, ax = plt.subplots(figsize=(10, 8))

    # Color mapping (red = overperformer, blue = underperformer, gray = neutral)
    colors = df['rank_diff'].apply(
        lambda x: '#d62728' if x > 0 else '#1f77b4' if x < 0 else '#7f7f7f'
    )

    # Scatter plot
    ax.scatter(
        df['control_rank'],
        df['centrality_rank_scatter'],
        c=colors,
        s=80,
        alpha=0.7,
        edgecolors='black',
        linewidth=0.5
    )

    # Diagonal reference line (perfect correspondence)
    ax.plot([0, 54], [0, 54], 'k--', alpha=0.3, linewidth=1,
            label=f'{control_name} = Centrality')

    # Label all states using adjustText
    texts = []
    for _, row in df.iterrows():
        x, y = row['control_rank'], row['centrality_rank_scatter']
        fontweight = 'bold' if abs(row['rank_diff']) >= label_threshold else 'normal'
        fontsize = 13 if abs(row['rank_diff']) >= label_threshold else 10
        t = ax.text(x, y, row['state_abbrev'],
                    fontsize=fontsize, fontweight=fontweight, ha='center', va='center')
        texts.append(t)

    adjust_text(texts, ax=ax,
                arrowprops=dict(arrowstyle='-', color='gray', alpha=0.4, lw=0.5),
                expand=(1.5, 1.5),
                force_text=(0.8, 0.8),
                force_points=(0.5, 0.5))

    # Axes and labels
    ax.set_xlabel(f'{control_name} Rank ({control_unit})  \u2190 Larger', fontsize=17)
    ax.set_ylabel(f'{measure_display} Centrality Rank (51\u00d751)  \u2190 More Central',
                  fontsize=17)
    ax.set_title(
        f'{control_name} vs. {measure_display} Centrality',
        fontsize=19,
        fontweight='bold',
        pad=15
    )

    # Invert axes (rank 1 = best)
    ax.invert_xaxis()
    ax.invert_yaxis()

    # Axis limits
    ax.set_xlim(54, -2)
    ax.set_ylim(54, -2)

    # Grid
    ax.grid(True, alpha=0.3)

    # Spearman annotation box (lower-right, committee.py style)
    stats_text = f"\u03c1 = {rho:.3f}"
    ax.text(0.97, 0.03, stats_text,
            transform=ax.transAxes, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                      alpha=0.9, edgecolor='gray', linewidth=1.5),
            fontsize=14, fontweight='bold', family='monospace')

    # Legend
    legend_elements = [
        Patch(facecolor='#d62728', label=f'Overperformer (Centrality > {control_name})'),
        Patch(facecolor='#1f77b4', label=f'Underperformer (Centrality < {control_name})'),
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

    print(f"\u2713 Scatter plot saved: {output_path}")
    print(f"\u2713 PDF version saved: {output_path.with_suffix('.pdf')}")

    return rho, p_value
